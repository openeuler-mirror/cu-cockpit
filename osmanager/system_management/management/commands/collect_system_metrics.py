from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '采集 cu-cockpit 历史指标并评估告警'
