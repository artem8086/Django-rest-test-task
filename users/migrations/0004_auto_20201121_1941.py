# Generated by Django 3.1.3 on 2020-11-21 16:41

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20201121_1849'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='subscribers',
        ),
        migrations.AddField(
            model_name='user',
            name='subscriptions',
            field=models.ManyToManyField(blank=True, related_name='_user_subscriptions_+', to=settings.AUTH_USER_MODEL),
        ),
    ]
