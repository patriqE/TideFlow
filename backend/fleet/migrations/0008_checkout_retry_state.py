from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fleet", "0007_booking_expiry")]
    operations = [
        migrations.AddField(model_name="booking", name="payment_access_code", field=models.CharField(max_length=255, blank=True)),
        migrations.AddField(model_name="booking", name="checkout_started_at", field=models.DateTimeField(null=True, blank=True)),
    ]
