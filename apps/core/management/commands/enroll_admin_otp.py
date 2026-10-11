"""Enroll an admin user in TOTP two-factor auth (plus one-time backup codes).

Run this on the server *before* relying on ADMIN_REQUIRE_OTP (on by default
in production), otherwise the admin can't log in at all:

    python manage.py enroll_admin_otp <username>

Prints a QR code to scan with any authenticator app (Aegis, 1Password,
Google Authenticator, ...), then asks for a current code to confirm the scan
worked. Only a confirmed device is ever saved as usable, so a bad scan can't
lock the owner out. Backup codes are shown exactly once.
"""

import contextlib
import io
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

BACKUP_CODE_COUNT = 10


class Command(BaseCommand):
    help = "Enroll an admin user in TOTP two-factor authentication."

    def add_arguments(self, parser) -> None:
        parser.add_argument("username")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Replace the user's existing OTP devices (e.g. a lost phone).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=options["username"])
        except user_model.DoesNotExist as exc:
            raise CommandError(f"No user named {options['username']!r}.") from exc
        if not user.is_staff:
            raise CommandError("Only staff users can be enrolled for admin OTP.")

        existing = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        if existing and not options["reset"]:
            raise CommandError(
                "User already has a confirmed TOTP device. Use --reset to replace it."
            )

        device = TOTPDevice(user=user, name="Authenticator", confirmed=False)
        self._show_qr(device.config_url)

        code = input("Enter the 6-digit code from your authenticator app to confirm: ").strip()
        # verify_token() persists throttling/drift state, so the device has to
        # exist in the DB first; it stays unconfirmed (unusable) until verified.
        with transaction.atomic():
            device.save()
            if not device.verify_token(code):
                raise CommandError(
                    "That code didn't match. Nothing was saved; run the command again."
                )

            if options["reset"]:
                TOTPDevice.objects.filter(user=user).exclude(pk=device.pk).delete()
                StaticDevice.objects.filter(user=user).delete()
            device.confirmed = True
            device.save()
            backup_codes = self._create_backup_codes(user)

        self.stdout.write(self.style.SUCCESS(f"TOTP enabled for {user.get_username()}."))
        self.stdout.write("One-time backup codes (store them offline, shown only once):")
        for token in backup_codes:
            self.stdout.write(f"  {token}")

    def _show_qr(self, url: str) -> None:
        # The QR is a convenience; the URL printed below is always enough.
        with contextlib.suppress(Exception):
            import qrcode

            qr = qrcode.QRCode(border=1)
            qr.add_data(url)
            buffer = io.StringIO()
            qr.print_ascii(out=buffer, invert=True)
            self.stdout.write(buffer.getvalue())
        self.stdout.write(f"Or enter this URL manually in your authenticator app:\n{url}\n")

    @staticmethod
    def _create_backup_codes(user) -> list[str]:
        static_device, _ = StaticDevice.objects.get_or_create(user=user, name="Backup codes")
        static_device.token_set.all().delete()
        tokens = [StaticToken.random_token() for _ in range(BACKUP_CODE_COUNT)]
        StaticToken.objects.bulk_create(StaticToken(device=static_device, token=t) for t in tokens)
        return tokens
