from django.core.management.base import BaseCommand
from apps.users.services.bootstrap_service import seed_accounts


class Command(BaseCommand):
    help = "Create missing sample accounts with unusable passwords; preserve existing accounts."

    def handle(self, *args, **options):
        seed_accounts()
        self.stdout.write(self.style.SUCCESS(
            "Missing accounts provisioned without passwords. Existing accounts preserved. "
            "Use set_account_password explicitly to provision a password."
        ))
