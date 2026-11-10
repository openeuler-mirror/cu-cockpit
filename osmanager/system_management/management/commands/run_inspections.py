"""One-shot entry point for the persistent inspection worker."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Queue due inspection plans and process one persisted run'
