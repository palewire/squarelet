# Generated by Django 2.1.7 on 2019-02-22 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_user_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_agency',
            field=models.BooleanField(default=False, help_text='This is an account used for allowing agencies to log in to the site', verbose_name='agency user'),
        ),
    ]
