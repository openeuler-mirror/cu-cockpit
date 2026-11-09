from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('system_management', '0009_inspectionplan')]

    operations = [migrations.CreateModel(
        name='InspectionRun',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                       serialize=False, verbose_name='ID')),
            ('plan_snapshot', models.JSONField(default=dict)),
            ('trigger', models.CharField(max_length=16, choices=[
                ('manual', 'Manual'), ('scheduled', 'Scheduled'),
            ])),
            ('actor', models.CharField(max_length=150)),
            ('template_id', models.CharField(max_length=32)),
            ('version', models.CharField(max_length=16)),
            ('parameters', models.JSONField(default=dict)),
            ('phase', models.CharField(db_index=True, default='queued', max_length=16,
                                      choices=[('queued', 'Queued'), ('running', 'Running'),
                                               ('finished', 'Finished')])),
            ('health', models.CharField(blank=True, null=True, max_length=16, choices=[
                (value, value.title()) for value in ('pass', 'warning', 'fail', 'error', 'skipped')
            ])),
            ('scheduled_slot', models.DateTimeField(blank=True, null=True)),
            ('queued_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ('started_at', models.DateTimeField(blank=True, null=True)),
            ('finished_at', models.DateTimeField(blank=True, db_index=True, null=True)),
            ('duration', models.FloatField(blank=True, null=True)),
            ('items', models.JSONField(default=list)),
            ('error', models.CharField(blank=True, max_length=512)),
            ('plan', models.ForeignKey(blank=True, null=True, related_name='runs',
                                      on_delete=django.db.models.deletion.SET_NULL,
                                      to='system_management.inspectionplan')),
        ],
        options={'ordering': ['-queued_at', '-id'], 'constraints': [
            models.UniqueConstraint(fields=('plan', 'scheduled_slot'),
                                    name='inspection_plan_slot_once'),
            models.UniqueConstraint(fields=('plan',), condition=models.Q(
                phase__in=['queued', 'running']), name='inspection_plan_active_once'),
            models.UniqueConstraint(fields=('phase',), condition=models.Q(phase='running'),
                                    name='inspection_single_running'),
        ]},
    )]