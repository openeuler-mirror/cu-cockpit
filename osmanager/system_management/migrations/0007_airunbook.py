from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('system_management', '0006_alertevent')]

    operations = [
        migrations.CreateModel(
            name='AIRunbook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor', models.CharField(db_index=True, max_length=150)),
                ('title', models.CharField(max_length=256)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('running', 'Running'), ('paused', 'Paused'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], db_index=True, default='draft', max_length=16)),
                ('current_step', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('error', models.TextField(blank=True)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]