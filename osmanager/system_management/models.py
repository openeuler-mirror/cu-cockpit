from django.db import models


class OperationAudit(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.CharField(max_length=150)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    module = models.CharField(max_length=64, db_index=True)
    action = models.CharField(max_length=96)
    target = models.CharField(max_length=512, blank=True)
    success = models.BooleanField(default=False, db_index=True)
    message = models.TextField(blank=True)
    detail = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']


class ConfigSnapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.CharField(max_length=150)
    module = models.CharField(max_length=64, db_index=True)
    target = models.CharField(max_length=128, db_index=True)
    path = models.CharField(max_length=1024)
    checksum = models.CharField(max_length=64)
    content = models.TextField()
    reason = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']


class CronJob(models.Model):
    name = models.CharField(max_length=128, unique=True)
    schedule = models.CharField(max_length=128)
    command = models.JSONField(default=list)
    enabled = models.BooleanField(default=True, db_index=True)
    created_by = models.CharField(max_length=150)
    updated_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name', 'id']


class CronExecution(models.Model):
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    )

    job = models.ForeignKey(CronJob, null=True, blank=True, on_delete=models.SET_NULL, related_name='executions')
    job_name = models.CharField(max_length=128)
    actor = models.CharField(max_length=150)
    manual = models.BooleanField(default=False, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='running', db_index=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    returncode = models.IntegerField(null=True, blank=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at', '-id']