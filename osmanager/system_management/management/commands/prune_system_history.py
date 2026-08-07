from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ...models import OperationAudit


class Command(BaseCommand):
    help = 'Delete expired system management history records.'

    def add_arguments(self, parser):
        parser.add_argument('--audit-days', type=int, default=90)

    def handle(self, *args, **options):
        days = options['audit_days']
        if days < 1:
            raise CommandError('--audit-days must be at least 1')
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = OperationAudit.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} expired audit records'))
