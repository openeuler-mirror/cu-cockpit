from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('system_management', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='CronJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('schedule', models.CharField(max_length=128)),
                ('command', models.JSONField(default=list)),
                ('enabled', models.BooleanField(db_index=True, default=True)),
                ('created_by', models.CharField(max_length=150)),
                ('updated_by', models.CharField(max_length=150)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_run_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={'ordering': ['name', 'id']},
        ),
        migrations.CreateModel(
            name='CronExecution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_name', models.CharField(max_length=128)),
                ('actor', models.CharField(max_length=150)),
                ('manual', models.BooleanField(db_index=True, default=False)),
                ('status', models.CharField(choices=[('running', 'Running'), ('success', 'Success'), ('failed', 'Failed'), ('timeout', 'Timeout')], db_index=True, default='running', max_length=16)),
                ('started_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('returncode', models.IntegerField(blank=True, null=True)),
                ('stdout', models.TextField(blank=True)),
                ('stderr', models.TextField(blank=True)),
                ('duration_ms', models.PositiveIntegerField(default=0)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='executions', to='system_management.cronjob')),
            ],
            options={'ordering': ['-started_at', '-id']},
        ),
    ]