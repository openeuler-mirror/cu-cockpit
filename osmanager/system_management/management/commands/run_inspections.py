"""One-shot entry point for the persistent inspection worker."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Queue due inspection plans and process one persisted run'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true',
                            help='Queue due plans and process at most one run, then exit (default)')
