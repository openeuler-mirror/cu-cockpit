from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('system_management', '0002_cronjob_cronexecution')]

    operations = [
        migrations.CreateModel(
            name='AIOperationPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor', models.CharField(db_index=True, max_length=150)),
                ('request_text', models.TextField()),
                ('intent', models.CharField(max_length=256)),
                ('summary', models.TextField(blank=True)),
                ('risk', models.CharField(db_index=True, default='readonly', max_length=16)),
                ('tool_calls', models.JSONField(default=list)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('executed', 'Executed'), ('failed', 'Failed')], db_index=True, default='draft', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('executed_at', models.DateTimeField(blank=True, null=True)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('error', models.TextField(blank=True)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]