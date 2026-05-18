from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('concept_analytics', '0002_alter_analyticsevent_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManifestSyncState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(blank=True, max_length=64)),
                ('synced_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Manifest sync state',
            },
        ),
    ]
