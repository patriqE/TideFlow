from datetime import timedelta

from django.db import migrations, models
import fleet.models


def populate_expiry(apps, schema_editor):
    Booking = apps.get_model("fleet", "Booking")
    for booking in Booking.objects.using(schema_editor.connection.alias).all().iterator():
        Booking.objects.using(schema_editor.connection.alias).filter(pk=booking.pk).update(
            expires_at=booking.created_at + timedelta(minutes=15),
        )


class Migration(migrations.Migration):
    dependencies = [("fleet", "0006_booking_seat_lookup_index")]
    operations = [
        migrations.AddField(model_name="booking", name="expires_at", field=models.DateTimeField(null=True)),
        migrations.RunPython(populate_expiry, migrations.RunPython.noop),
        migrations.AlterField(model_name="booking", name="expires_at",
                              field=models.DateTimeField(default=fleet.models.booking_expiry, db_index=True)),
    ]
