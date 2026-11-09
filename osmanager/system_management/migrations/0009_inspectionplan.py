from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('system_management', '0008_airunbookstep')]

    operations = [migrations.CreateModel(
        name='InspectionPlan',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                       serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=128)),
            ('template_id', models.CharField(default='local-host', max_length=32)),
            ('version', models.CharField(default='v1', max_length=16)),
            ('parameters', models.JSONField(default=dict)),
            ('schedule_kind', models.CharField(default='manual', max_length=16, choices=[
                ('manual', 'Manual'), ('daily', 'Daily'), ('interval', 'Interval'),
            ])),
            ('enabled', models.BooleanField(db_index=True, default=False)),
            ('timezone', models.CharField(default='Asia/Shanghai', max_length=64)),
            ('schedule_settings', models.JSONField(default=dict)),
            ('revision', models.PositiveIntegerField(default=1)),
            ('next_run', models.DateTimeField(blank=True, db_index=True, null=True)),
            ('cursor', models.DateTimeField(blank=True, null=True)),
            ('actor', models.CharField(max_length=150)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ],
        options={'ordering': ['name', 'id']},
    )]