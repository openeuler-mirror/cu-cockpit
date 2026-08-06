from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('system_management', '0005_alertrule')]

    operations = [
        migrations.CreateModel(
            name='AlertEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('active', 'Active'), ('recovered', 'Recovered')], db_index=True, default='active', max_length=16)),
                ('started_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('recovered_at', models.DateTimeField(blank=True, null=True)),
                ('trigger_value', models.FloatField()),
                ('last_value', models.FloatField()),
                ('recovery_value', models.FloatField(blank=True, null=True)),
                ('acknowledged_by', models.CharField(blank=True, max_length=150)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('context', models.JSONField(blank=True, default=dict)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='system_management.alertrule')),
            ],
            options={'ordering': ['-started_at', '-id']},
        ),
        migrations.AddConstraint(
            model_name='alertevent',
            constraint=models.UniqueConstraint(condition=models.Q(status='active'), fields=('rule',), name='one_active_event_per_rule'),
        ),
    ]