# Generated by Django 5.1.5 on 2025-02-05 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empPortal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_gen_id', models.CharField(max_length=255)),
                ('user_name', models.CharField(max_length=255)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255)),
                ('role_name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.RemoveField(
            model_name='roles',
            name='roleId',
        ),
    ]
