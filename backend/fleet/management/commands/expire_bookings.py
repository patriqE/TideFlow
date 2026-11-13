from django.core.management.base import BaseCommand

from fleet.expiry import expire_unpaid_bookings


class Command(BaseCommand):
    help = "Close expired unpaid reservations; safe to run repeatedly."

    def handle(self, *args, **options):
        count = expire_unpaid_bookings()
        self.stdout.write(f"Expired {count} unpaid booking(s).")
