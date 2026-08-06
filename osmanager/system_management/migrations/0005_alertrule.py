from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('system_management', '0004_metricsample')]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('metric', models.CharField(choices=[('cpu_percent', 'CPU'), ('memory_percent', 'Memory'), ('root_percent', 'Root filesystem'), ('inode_percent', 'Root inode')], db_index=True, max_length=32)),
                ('operator', models.CharField(choices=[('gte', '>='), ('lte', '<=')], default='gte', max_length=8)),
                ('threshold', models.FloatField()),
                ('recovery_threshold', models.FloatField()),
                ('consecutive_hits', models.PositiveSmallIntegerField(default=3)),
                ('enabled', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name', 'id']},
        ),
    ]