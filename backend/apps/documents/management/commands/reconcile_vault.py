import json
from django.core.management.base import BaseCommand
from apps.documents.services.recovery_service import reconcile_vault


class Command(BaseCommand):
    help = "Dry-run vault recovery by default; explicit --apply removes unreferenced generated files only."

    def add_arguments(self, parser):
        parser.add_argument("--grace-seconds", type=int, required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        result = reconcile_vault(options["grace_seconds"], options["apply"])
        self.stdout.write(json.dumps(result))
