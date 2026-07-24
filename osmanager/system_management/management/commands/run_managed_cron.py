from django.core.management.base import BaseCommand, CommandError

from osmanager.system_management.cron import execute_job
from osmanager.system_management.models import CronJob


class Command(BaseCommand):
    help = '执行 cu-cockpit 管理的 Cron 任务'

    def add_arguments(self, parser):
        parser.add_argument('job_id', type=int)

    def handle(self, *args, **options):
        try:
            job = CronJob.objects.get(id=options['job_id'], enabled=True)
        except CronJob.DoesNotExist as error:
            raise CommandError('任务不存在或已停用') from error
        execution = execute_job(job, actor='cron', manual=False)
        if execution.status != 'success':
            raise CommandError(f'任务执行状态: {execution.status}')
        self.stdout.write(self.style.SUCCESS(f'任务 {job.id} 执行成功'))