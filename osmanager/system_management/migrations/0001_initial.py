from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ConfigSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.CharField(max_length=150)),
                ('module', models.CharField(db_index=True, max_length=64)),
                ('target', models.CharField(db_index=True, max_length=128)),
                ('path', models.CharField(max_length=1024)),
                ('checksum', models.CharField(max_length=64)),
                ('content', models.TextField()),
                ('reason', models.CharField(blank=True, max_length=512)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
        migrations.CreateModel(
            name='OperationAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.CharField(max_length=150)),
                ('client_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('module', models.CharField(db_index=True, max_length=64)),
                ('action', models.CharField(max_length=96)),
                ('target', models.CharField(blank=True, max_length=512)),
                ('success', models.BooleanField(db_index=True, default=False)),
                ('message', models.TextField(blank=True)),
                ('detail', models.JSONField(blank=True, default=dict)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]