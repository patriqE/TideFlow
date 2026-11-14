from django.db import migrations, models


def copy_existing_names(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    for profile in Profile.objects.using(schema_editor.connection.alias).select_related("user").iterator():
        name = f"{profile.user.first_name} {profile.user.last_name}".strip()[:255]
        if name:
            Profile.objects.using(schema_editor.connection.alias).filter(pk=profile.pk).update(full_name=name)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_add_role_field")]
    operations = [
        migrations.AddField(model_name="profile", name="full_name", field=models.CharField(max_length=255, blank=True)),
        migrations.RunPython(copy_existing_names, migrations.RunPython.noop),
    ]
