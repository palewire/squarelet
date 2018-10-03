# Generated by Django 2.0.6 on 2018-10-03 16:52

import autoslug.fields
import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import squarelet.core.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name of organization')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='name', verbose_name='slug')),
                ('created_at', squarelet.core.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('updated_at', squarelet.core.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='updated at')),
                ('org_type', models.IntegerField(choices=[(0, 'Free'), (1, 'Pro'), (2, 'Basic'), (3, 'Plus')], default=2, verbose_name='organization type')),
                ('individual', models.BooleanField(default=False, help_text='This organization is solely for the use of one user', verbose_name='individual organization')),
                ('private', models.BooleanField(default=False, verbose_name='private organization')),
                ('max_users', models.IntegerField(default=1, verbose_name='maximum users')),
                ('monthly_cost', models.IntegerField(default=0, help_text='In cents', verbose_name='monthly cost')),
                ('date_update', models.DateField(default=datetime.date.today, help_text='Date when monthly requests are restored', verbose_name='date update')),
                ('requests_per_month', models.IntegerField(default=0, help_text='Number of requests this organization receives each month.', verbose_name='requests per month')),
                ('monthly_requests', models.IntegerField(default=0, help_text='How many recurring requests are left for this month.', verbose_name='monthly requests')),
                ('num_requests', models.IntegerField(default=0, help_text='How many non-recurring requests are left.', verbose_name='number of requests')),
                ('pages_per_month', models.IntegerField(default=0, help_text='Number of pages this organization receives each month.', verbose_name='pages per month')),
                ('monthly_pages', models.IntegerField(default=0, help_text='How many recurring pages are left for this month.', verbose_name='monthly pages')),
                ('num_pages', models.IntegerField(default=0, help_text='How many non-recurring pages are left.', verbose_name='number of pages')),
                ('customer_id', models.CharField(blank=True, max_length=255, verbose_name='customer id')),
                ('subscription_id', models.CharField(blank=True, max_length=255, verbose_name='subscription id')),
                ('payment_failed', models.BooleanField(default=False, verbose_name='payment failed')),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin', models.BooleanField(default=False, help_text='This user has administrative rights for this organization', verbose_name='admin')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.Organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReceiptEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipt_emails', to='organizations.Organization')),
            ],
        ),
        migrations.AddField(
            model_name='organization',
            name='users',
            field=models.ManyToManyField(related_name='organizations', through='organizations.OrganizationMembership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='organizationmembership',
            unique_together={('user', 'organization')},
        ),
    ]
