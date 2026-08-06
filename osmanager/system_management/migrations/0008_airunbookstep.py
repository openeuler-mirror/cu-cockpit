from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('system_management', '0007_airunbook')]

    operations = [
        migrations.CreateModel(
            name='AIRunbookStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField()),
                ('title', models.CharField(max_length=256)),
                ('tool_call', models.JSONField(default=dict)),
                ('risk', models.CharField(default='readonly', max_length=16)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('awaiting_confirmation', 'Awaiting confirmation'), ('running', 'Running'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('skipped', 'Skipped'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=32)),
                ('output', models.JSONField(blank=True, default=dict)),
                ('error', models.TextField(blank=True)),
                ('confirmation_token_hash', models.CharField(blank=True, max_length=64)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('runbook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='system_management.airunbook')),
            ],
            options={'ordering': ['position', 'id']},
        ),
        migrations.AddConstraint(
            model_name='airunbookstep',
            constraint=models.UniqueConstraint(fields=('runbook', 'position'), name='unique_runbook_step_position'),
        ),
    ]