from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('system_management', '0003_aioperationplan')]

    operations = [
        migrations.CreateModel(
            name='MetricSample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collected_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('cpu_percent', models.FloatField(blank=True, null=True)),
                ('memory_percent', models.FloatField(blank=True, null=True)),
                ('root_percent', models.FloatField(blank=True, null=True)),
                ('inode_percent', models.FloatField(blank=True, null=True)),
                ('network_rx_bytes', models.BigIntegerField(blank=True, null=True)),
                ('network_tx_bytes', models.BigIntegerField(blank=True, null=True)),
                ('services', models.JSONField(blank=True, default=dict)),
            ],
            options={'ordering': ['-collected_at', '-id']},
        ),
    ]