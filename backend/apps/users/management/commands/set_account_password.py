"""Explicit operator provisioning; never invoked by ordinary seeding."""
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import APIException

from apps.users.models import CustomUser
from apps.users.services.user_service import update_user


class Command(BaseCommand):
    help = "Explicitly set an account password interactively and revoke its login sessions."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        try:
            user = CustomUser.objects.get(username=options["username"])
        except CustomUser.DoesNotExist as exc:
            raise CommandError("Account does not exist.") from exc
        password = getpass("New password: ")
        if password != getpass("Confirm password: "):
            raise CommandError("Passwords do not match.")
        try:
            update_user(None, user, {"password": password})
        except APIException as exc:
            raise CommandError("Password update failed validation or audit recording.") from exc
        self.stdout.write(self.style.SUCCESS("Password updated; existing sessions revoked."))
