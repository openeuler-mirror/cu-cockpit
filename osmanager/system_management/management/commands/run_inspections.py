"""One-shot entry point for the persistent inspection worker."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Queue due inspection plans and process one persisted run'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true',
                            help='Queue due plans and process at most one run, then exit (default)')

    def handle(self, *args, **options):
        import json
        from django.core.management.base import CommandError
        from django.core.serializers.json import DjangoJSONEncoder
        from osmanager.system_management.inspection_jobs import queue_due, run_next
        from osmanager.system_management.inspection_reports import serialize_run

        try:
            queued = queue_due()
            completed = run_next()
            self.stdout.write(json.dumps({
                'queued': len(queued),
                'run': serialize_run(completed) if completed is not None else None,
            }, cls=DjangoJSONEncoder, ensure_ascii=False, allow_nan=False))
        except Exception as error:
            raise CommandError(f'Inspection worker failed: {error}') from error
