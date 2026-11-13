from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fleet", "0005_alter_booking_payment_currency_and_more")]

    operations = [
        migrations.AddIndex(
            model_name="booking",
            index=models.Index(fields=["schedule", "ride_date", "status"], name="booking_seat_lookup_idx"),
        ),
    ]
