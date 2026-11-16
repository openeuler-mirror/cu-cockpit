"""Backup HTTP contracts through the production URL configuration."""

import io
import json
import os
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path
from subprocess import run as run_local_node
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from osmanager.system_management.backup_center import (
    create_backup_archive, initialize_installation, read_backup_index, write_backup_index,
)
from osmanager.system_management.backup_runtime import BACKUP_COMPAT_VERSION
from osmanager.system_management.backup_restore import _pause_services
from osmanager.system_management.config_center import CHRONY_TARGET
from osmanager.system_management.models import OperationAudit


class BackupAPITest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.base = '/api/system/backups/'
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.root = self.directory / 'backups'
        self.root.mkdir(mode=0o700)
        self.database = self.directory / 'source.sqlite3'
        with closing(sqlite3.connect(self.database)) as database:
            database.execute('CREATE TABLE data (value TEXT)')
            database.execute('INSERT INTO data VALUES (?)', ('saved',))
            database.commit()
        self.config = self.directory / 'chrony.conf'
        self.config.write_bytes(b'pool example.invalid\n')
        self.units = self.directory / 'units'
        self.units.mkdir()
        (self.units / 'cu-cockpit.service').touch()
        self.enterContext(patch.dict(os.environ, {
            'BACKUP_ROOT': str(self.root), 'BACKUP_RESTORE_SERVICES': 'cu-cockpit.service'}))
        self.enterContext(patch('osmanager.system_management.backup_runtime.CHRONY_PATH',
                                self.config))
        self.enterContext(patch('osmanager.system_management.backup_runtime.registered_targets',
                                return_value={CHRONY_TARGET: str(self.config)}))
        self.enterContext(patch('osmanager.system_management.backup_views.backup_database',
                                return_value=self.database))
        self.enterContext(patch('osmanager.system_management.backup_restore.SYSTEMD_UNIT_DIRS',
                                (self.units,)))
        self.account = self.enterContext(patch(
            'osmanager.system_management.permissions.pwd.getpwnam',
            return_value=SimpleNamespace(pw_uid=0)))
        self.worker = self.enterContext(patch(
            'osmanager.system_management.backup_jobs.run_pending',
            side_effect=AssertionError('HTTP must not run the backup worker')))
        self.restore = self.enterContext(patch(
            'osmanager.system_management.backup_restore.restore_confirmed',
            side_effect=AssertionError('HTTP must not execute restore')))
        self.systemctl = self.enterContext(patch(
            'subprocess.run', side_effect=AssertionError('HTTP must not invoke systemctl')))
        initialize_installation(self.root, BACKUP_COMPAT_VERSION)

    def login(self, uid=0):
        self.account.return_value = SimpleNamespace(pw_uid=uid)
        session = self.client.session
        session['username'] = 'operator'
        session.save()
        response = self.client.get(self.base + 'overview')
        self.assertEqual(response.status_code, 200 if uid == 0 else 403)
        if uid == 0:
            self.assertIn('csrftoken', response.cookies)
            return self.client.cookies['csrftoken'].value
        return None

    def post_json(self, path, payload, token):
        return self.client.post(self.base + path, json.dumps(payload),
                                content_type='application/json', HTTP_X_CSRFTOKEN=token)

    def archive(self):
        return create_backup_archive(self.root, self.database,
                                     {CHRONY_TARGET: self.config}, BACKUP_COMPAT_VERSION,
                                     'operator')

    def test_permissions_and_csrf_apply_to_all_endpoints(self):
        paths = ('create', 'import', 'schedule', 'verify', 'restore/preflight',
                 'restore/confirm', 'download/' + 'a' * 32)
        self.assertEqual(self.client.get(self.base + 'overview').status_code, 401)
        for path in paths:
            with self.subTest(path=path):
                response = (self.client.get(self.base + path) if path.startswith('download/')
                            else self.client.post(self.base + path, '{}',
                                                  content_type='application/json'))
                self.assertEqual(response.status_code, 401 if path == 'import' or
                                 path.startswith('download/') else 403)
        token = self.login()
        self.login(uid=1000)
        self.assertEqual(self.client.get(self.base + 'download/' + 'a' * 32).status_code, 403)
        self.assertEqual(self.client.post(self.base + 'create', '{}',
                                          content_type='application/json').status_code, 403)
        self.assertEqual(self.post_json('create', {}, token).status_code, 403)
        token = self.login()
        self.assertEqual(self.client.post(self.base + 'create', '{}',
                                          content_type='application/json').status_code, 403)
        self.assertEqual(self.post_json('create', {}, token).status_code, 202)
        self.assertEqual(len(read_backup_index(self.root)['tasks']), 1)
        self.worker.assert_not_called()
        self.restore.assert_not_called()
        self.systemctl.assert_not_called()

    def test_overview_exposes_status_not_private_metadata(self):
        token = self.login()
        self.post_json('create', {}, token)
        record = self.archive()
        index = read_backup_index(self.root)
        index['tasks']['a' * 32] = {
            'id': 'a' * 32, 'kind': 'restore', 'status': 'manual_recovery_required',
            'phase': 'rollback', 'error': '/private/secret/restore.db',
            'requires_manual_recovery': True, 'safety_archive_id': record['archive_id'],
            'token_hash': 'never-expose-me', 'archive_hash': 'private-digest',
            'targets': {'app.sqlite3': '/private/secret/restore.db'},
        }
        write_backup_index(self.root, index)
        response = self.client.get(self.base + 'overview')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        for secret in ('hmac_key', 'token_hash', 'never-expose-me', 'private-digest',
                       '/private/secret', 'targets', 'signature'):
            self.assertNotIn(secret, body)
        task = next(item for item in response.json()['tasks'] if item['kind'] == 'restore')
        self.assertEqual(task['status'], 'manual_recovery_required')
        self.assertEqual(task['phase'], 'rollback')
        self.assertTrue(task['requires_manual_recovery'])
        self.assertEqual(task['safety_archive_id'], record['archive_id'])

    def test_signed_archive_verify_download_and_schedule(self):
        token = self.login()
        record = self.archive()
        archive_id = record['archive_id']
        verified = self.post_json('verify', {'archive_id': archive_id}, token)
        self.assertEqual(verified.status_code, 200)
        self.assertEqual(set(verified.json()['members']),
                         {'app.sqlite3', f'configs/{CHRONY_TARGET}.bin'})
        download = self.client.get(self.base + 'download/' + archive_id)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b''.join(download.streaming_content),
                         (self.root / f'{archive_id}.zip').read_bytes())
        self.assertEqual(download['Cache-Control'], 'private, no-store')
        schedule = self.post_json('schedule', {
            'enabled': True, 'time': '02:30', 'timezone': 'UTC'}, token)
        self.assertEqual(schedule.status_code, 200)
        self.assertTrue(self.client.get(self.base + 'overview').json()['schedule']['enabled'])
        self.worker.assert_not_called()

    def test_ui_schedule_body_passes_strict_endpoint_without_readonly_fields(self):
        token = self.login()
        script = Path(__file__).parent / 'frontend' / 'backup-workspace.test.cjs'
        body = json.loads(run_local_node(
            ['node', str(script), '--schedule-body'], capture_output=True,
            text=True, timeout=15, check=True).stdout)
        self.assertEqual(body, {'enabled': True, 'time': '02:30', 'timezone': 'UTC'})
        response = self.post_json('schedule', body, token)
        self.assertEqual(response.status_code, 200)
        self.assertIn('next_run', response.json()['schedule'])
        self.assertEqual(self.post_json('schedule', {
            **body, 'next_run': response.json()['schedule']['next_run']}, token).status_code, 400)

    def test_import_rejects_bad_zip_and_oversized_request(self):
        token = self.login()
        bad = SimpleUploadedFile('backup.zip', b'not a ZIP file')
        response = self.client.post(self.base + 'import', {'file': bad},
                                    HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 422)
        huge = SimpleUploadedFile('backup.zip', b'x' * (1024 * 1024 + 1024))
        with patch('osmanager.system_management.backup_views.MAX_ARCHIVE_BYTES', 1):
            response = self.client.post(self.base + 'import', {'file': huge},
                                        HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(read_backup_index(self.root)['backups'] if
                         (self.root / 'index.json').exists() else {})

    def test_import_gate_rejects_without_parsing_multipart(self):
        token = self.login()
        self.client.cookies.pop('sessionid', None)
        upload = b'x' * (3 * 1024 * 1024)

        def rejected(expected, **headers):
            with patch('django.http.request.HttpRequest._load_post_and_files',
                       side_effect=AssertionError('multipart parsed')) as parse, patch(
                       'django.core.files.uploadhandler.TemporaryFileUploadHandler.receive_data_chunk',
                       side_effect=AssertionError('upload written')) as write:
                response = self.client.post(self.base + 'import', {
                    'file': SimpleUploadedFile('backup.zip', upload)}, **headers)
            self.assertEqual(response.status_code, expected)
            parse.assert_not_called()
            write.assert_not_called()
            return response

        rejected(401, HTTP_X_CSRFTOKEN=token)
        self.login(uid=1000)
        rejected(403, HTTP_X_CSRFTOKEN=token)
        token = self.login()
        with patch('osmanager.system_management.backup_import_gate.MAX_ARCHIVE_BYTES',
                   2 * 1024 * 1024):
            rejected(400, HTTP_X_CSRFTOKEN=token)
        with patch('osmanager.system_management.backup_import_gate.MAX_ARCHIVE_BYTES',
                   2 * 1024 * 1024):
            rejected(400, HTTP_X_CSRFTOKEN='wrongtoken')
        rejected(400, HTTP_X_CSRFTOKEN=token, CONTENT_LENGTH='')
        rejected(400, HTTP_X_CSRFTOKEN=token, CONTENT_LENGTH='9' * 5000)
        denied = OperationAudit.objects.filter(module='system', action='permission_denied')
        self.assertTrue(denied.exists())
        self.assertNotIn(token, str(list(denied.values_list('detail', flat=True))))

    def test_import_gate_keeps_csrf_and_exact_path(self):
        token = self.login()
        response = self.client.post(self.base + 'import', {
            'file': SimpleUploadedFile('backup.zip', b'not a ZIP')})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'CSRF', response.content)
        self.assertEqual(self.client.post(self.base + 'import', {
            'file': SimpleUploadedFile('backup.zip', b'not a ZIP')},
            HTTP_X_CSRFTOKEN='wrongtoken').status_code, 403)
        self.assertEqual(self.client.post(self.base + 'import/', {
            'file': SimpleUploadedFile('backup.zip', b'not a ZIP')},
            HTTP_X_CSRFTOKEN=token).status_code, 404)

    @override_settings(DEBUG=True)
    def test_import_malformed_manifest_never_exposes_installation_key(self):
        token = self.login()
        record = self.archive()
        secret = json.loads((self.root / 'metadata.json').read_text())['hmac_key']
        with zipfile.ZipFile(self.root / f'{record["archive_id"]}.zip') as original:
            manifest = json.loads(original.read('manifest.json'))
            members = {name: original.read(name) for name in original.namelist()
                       if name != 'manifest.json'}

        for signature in ('é', 123, None, [], 'g' * 64, 'A' * 64):
            with self.subTest(signature=signature):
                modified = {**manifest, 'signature': signature}
                self._assert_invalid_import(token, members, json.dumps(modified).encode(), secret)
        for payload in (b'{', b'\xff'):
            with self.subTest(payload=payload):
                self._assert_invalid_import(token, members, payload, secret)
        self._assert_invalid_import(token, members, json.dumps(manifest).encode(), secret,
                                    compression=zipfile.ZIP_BZIP2)

    def _assert_invalid_import(self, token, members, manifest, secret,
                               compression=zipfile.ZIP_STORED):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', compression=compression) as package:
            package.writestr('manifest.json', manifest)
            for name, content in members.items():
                package.writestr(name, content)
        response = self.client.post(self.base + 'import', {
            'file': SimpleUploadedFile('backup.zip', archive.getvalue())},
            HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.content.decode())
        self.assertNotIn('Traceback', response.content.decode())

    def test_import_accepts_upload_at_request_limit(self):
        token = self.login()
        self.config.write_bytes(os.urandom(1024 * 1024))
        record = self.archive()
        content = (self.root / f'{record["archive_id"]}.zip').read_bytes()
        index = read_backup_index(self.root)
        index['backups'].clear()
        write_backup_index(self.root, index)
        (self.root / f'{record["archive_id"]}.zip').unlink()
        from django.test.client import BOUNDARY, encode_multipart

        request_size = len(encode_multipart(BOUNDARY, {
            'file': SimpleUploadedFile('backup.zip', content)}))
        with patch('osmanager.system_management.backup_import_gate.MAX_ARCHIVE_BYTES',
                   request_size - 1024 * 1024):
            response = self.client.post(self.base + 'import', {
                'file': SimpleUploadedFile('backup.zip', content)}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['backup']['archive_id'], record['archive_id'])

    def test_import_accepts_signed_archive_without_client_paths(self):
        token = self.login()
        record = self.archive()
        archive_id = record['archive_id']
        content = (self.root / f'{archive_id}.zip').read_bytes()
        (self.root / f'{archive_id}.zip').unlink()
        index = read_backup_index(self.root)
        index['backups'].clear()
        write_backup_index(self.root, index)
        response = self.client.post(self.base + 'import', {
            'file': SimpleUploadedFile('backup.zip', content)}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['backup']['archive_id'], archive_id)
        self.assertIn(archive_id, read_backup_index(self.root)['backups'])

    def test_download_rechecks_archive_after_verification(self):
        token = self.login()
        archive_id = self.archive()['archive_id']
        from osmanager.system_management import backup_views

        original = backup_views._registered_archive

        def remove_after_validation(*args):
            result = original(*args)
            (self.root / f'{archive_id}.zip').unlink()
            return result

        with patch.object(backup_views, '_registered_archive', side_effect=remove_after_validation):
            response = self.client.get(self.base + 'download/' + archive_id)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(str(self.root), response.content.decode())
        self.systemctl.assert_not_called()

    def test_preflight_confirm_replay_and_service_registry(self):
        token = self.login()
        archive_id = self.archive()['archive_id']
        preview = self.post_json('restore/preflight', {'archive_id': archive_id}, token)
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview.json()['preview']['requires_maintenance'])
        task_id = preview.json()['task_id']
        confirmation = {'task_id': task_id, 'token': preview.json()['token']}
        confirmed = self.post_json('restore/confirm', confirmation, token)
        self.assertEqual(confirmed.status_code, 202)
        self.assertEqual(confirmed.json()['task']['status'], 'awaiting_maintenance')
        self.assertEqual(self.post_json('restore/confirm', confirmation, token).status_code, 409)
        self.assertNotIn('token_hash', read_backup_index(self.root)['tasks'][task_id])
        self.assertEqual(self.client.get(self.base + 'overview').json()['tasks'][-1]['status'],
                         'awaiting_maintenance')
        self.assertNotIn(confirmation['token'], ' '.join(
            str((audit.target, audit.message, audit.detail)) for audit in
            OperationAudit.objects.filter(module='backup')))
        self.restore.assert_not_called()
        self.systemctl.assert_not_called()

    def test_invalid_requests_missing_storage_and_archive_race(self):
        token = self.login()
        for payload in ({'archive_id': '../etc/passwd'}, {'archive_id': 'a' * 32, 'path': '/etc'}):
            self.assertEqual(self.post_json('verify', payload, token).status_code, 400)
        self.assertEqual(self.client.get(self.base + 'download/../etc').status_code, 404)
        archive_id = self.archive()['archive_id']
        (self.root / f'{archive_id}.zip').unlink()
        self.assertEqual(self.post_json('restore/preflight',
                                        {'archive_id': archive_id}, token).status_code, 503)
        self.assertEqual(self.client.get(self.base + 'download/' + archive_id).status_code, 503)
        (self.root / 'index.json').unlink()
        self.assertEqual(self.post_json('verify', {'archive_id': archive_id}, token).status_code,
                         503)
        self.assertEqual(self.client.get(self.base + 'overview').status_code, 200)

    def test_bad_index_metadata_and_archive_never_expose_paths(self):
        token = self.login()
        record = self.archive()
        archive_id = record['archive_id']
        archive = self.root / f'{archive_id}.zip'
        with archive.open('r+b') as content:
            content.seek(0)
            content.write(b'BAD!')
        self.assertEqual(self.post_json('verify', {'archive_id': archive_id}, token).status_code,
                         422)
        self.assertEqual(self.client.get(self.base + 'download/' + archive_id).status_code, 422)
        (self.root / 'index.json').write_text('invalid JSON')
        self.assertEqual(self.client.get(self.base + 'overview').status_code, 503)
        self.assertEqual(self.post_json('create', {}, token).status_code, 503)
        (self.root / 'metadata.json').unlink()
        response = self.client.get(self.base + 'overview')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(str(self.root), response.content.decode())

    def test_preflight_requires_all_installed_writer_units(self):
        token = self.login()
        archive_id = self.archive()['archive_id']
        for name in ('cu-cockpit-inspection.service', 'cu-cockpit-inspection.timer',
                     'cu-cockpit-metrics.service', 'cu-cockpit-metrics.timer',
                     'cu-cockpit-backup.service', 'cu-cockpit-backup.timer'):
            (self.units / name).touch()
        response = self.post_json('restore/preflight', {'archive_id': archive_id}, token)
        self.assertEqual(response.status_code, 503)
        self.assertFalse(read_backup_index(self.root)['tasks'])
        with patch.dict(os.environ, {'BACKUP_RESTORE_SERVICES': ','.join(sorted(
                unit.name for unit in self.units.iterdir()))}):
            response = self.post_json('restore/preflight', {'archive_id': archive_id}, token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()['preview']['services']),
                         {unit.name for unit in self.units.iterdir()})

    def test_missing_unit_state_is_not_treated_as_inactive(self):
        controller = Mock()
        controller.is_active.return_value = 'unknown'
        with self.assertRaises(RuntimeError):
            _pause_services(controller, ['cu-cockpit.service'])
        controller.stop.assert_not_called()
        controller.start.assert_not_called()