# Generated by Django 5.1.5 on 2025-02-05 07:39

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empPortal', '0002_users_remove_roles_roleid'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='users',
            name='phone',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='users',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='empPortal.roles'),
        ),
        migrations.AddField(
            model_name='users',
            name='status',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='users',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
