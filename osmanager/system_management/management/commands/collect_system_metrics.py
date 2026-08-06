import os

from django.core.management.base import BaseCommand

from osmanager.system_management.monitoring import collect_metric_sample, purge_metric_samples


class Command(BaseCommand):
    help = '采集 cu-cockpit 历史指标并评估告警'

    def handle(self, *args, **options):
        sample = collect_metric_sample()
        deleted = purge_metric_samples(os.environ.get('METRIC_RETENTION_DAYS', '30'))
        self.stdout.write(self.style.SUCCESS(f'指标样本 {sample.id} 已保存，清理 {deleted} 条过期数据'))
