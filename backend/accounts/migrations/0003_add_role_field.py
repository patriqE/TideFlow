from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_session"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="role",
            field=models.CharField(choices=[('PASSENGER', 'Passenger'), ('DECK_AGENT', 'Deck Agent'), ('ADMIN', 'Admin')], default='PASSENGER', max_length=32),
        ),
    ]
