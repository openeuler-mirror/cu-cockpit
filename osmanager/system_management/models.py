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


class AIOperationPlan(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
    )

    actor = models.CharField(max_length=150, db_index=True)
    request_text = models.TextField()
    intent = models.CharField(max_length=256)
    summary = models.TextField(blank=True)
    risk = models.CharField(max_length=16, default='readonly', db_index=True)
    tool_calls = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at', '-id']


class MetricSample(models.Model):
    collected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cpu_percent = models.FloatField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    root_percent = models.FloatField(null=True, blank=True)
    inode_percent = models.FloatField(null=True, blank=True)
    network_rx_bytes = models.BigIntegerField(null=True, blank=True)
    network_tx_bytes = models.BigIntegerField(null=True, blank=True)
    services = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-collected_at', '-id']


class AlertRule(models.Model):
    METRIC_CHOICES = (
        ('cpu_percent', 'CPU'),
        ('memory_percent', 'Memory'),
        ('root_percent', 'Root filesystem'),
        ('inode_percent', 'Root inode'),
    )
    OPERATOR_CHOICES = (('gte', '>='), ('lte', '<='))

    name = models.CharField(max_length=128, unique=True)
    metric = models.CharField(max_length=32, choices=METRIC_CHOICES, db_index=True)
    operator = models.CharField(max_length=8, choices=OPERATOR_CHOICES, default='gte')
    threshold = models.FloatField()
    recovery_threshold = models.FloatField()
    consecutive_hits = models.PositiveSmallIntegerField(default=3)
    enabled = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'id']


class AlertEvent(models.Model):
    STATUS_CHOICES = (('active', 'Active'), ('recovered', 'Recovered'))

    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active', db_index=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    recovered_at = models.DateTimeField(null=True, blank=True)
    trigger_value = models.FloatField()
    last_value = models.FloatField()
    recovery_value = models.FloatField(null=True, blank=True)
    acknowledged_by = models.CharField(max_length=150, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-started_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['rule'], condition=models.Q(status='active'), name='one_active_event_per_rule'
            ),
        ]


class AIRunbook(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    actor = models.CharField(max_length=150, db_index=True)
    title = models.CharField(max_length=256)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft', db_index=True)
    current_step = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at', '-id']


class AIRunbookStep(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('awaiting_confirmation', 'Awaiting confirmation'),
        ('running', 'Running'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    )

    runbook = models.ForeignKey(AIRunbook, on_delete=models.CASCADE, related_name='steps')
    position = models.PositiveIntegerField()
    title = models.CharField(max_length=256)
    tool_call = models.JSONField(default=dict)
    risk = models.CharField(max_length=16, default='readonly')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending', db_index=True)
    output = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    confirmation_token_hash = models.CharField(max_length=64, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['position', 'id']
        constraints = [models.UniqueConstraint(fields=['runbook', 'position'], name='unique_runbook_step_position')]


class InspectionPlan(models.Model):
    name = models.CharField(max_length=128)
    template_id = models.CharField(max_length=32, default='local-host')
    version = models.CharField(max_length=16, default='v1')
    parameters = models.JSONField(default=dict)
    schedule_kind = models.CharField(max_length=16, default='manual', choices=[
        ('manual', 'Manual'), ('daily', 'Daily'), ('interval', 'Interval'),
    ])
    enabled = models.BooleanField(default=False, db_index=True)
    timezone = models.CharField(max_length=64, default='Asia/Shanghai')
    schedule_settings = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=1)
    next_run = models.DateTimeField(null=True, blank=True, db_index=True)
    cursor = models.DateTimeField(null=True, blank=True)
    actor = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'id']


class InspectionRun(models.Model):
    plan = models.ForeignKey(InspectionPlan, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='runs')
    plan_snapshot = models.JSONField(default=dict)
    trigger = models.CharField(max_length=16, choices=[
        ('manual', 'Manual'), ('scheduled', 'Scheduled'),
    ])
    actor = models.CharField(max_length=150)
    template_id = models.CharField(max_length=32)
    version = models.CharField(max_length=16)
    parameters = models.JSONField(default=dict)
    phase = models.CharField(max_length=16, default='queued', db_index=True, choices=[
        ('queued', 'Queued'), ('running', 'Running'), ('finished', 'Finished'),
    ])
    health = models.CharField(max_length=16, null=True, blank=True, choices=[
        (value, value.title()) for value in ('pass', 'warning', 'fail', 'error', 'skipped')
    ])
    scheduled_slot = models.DateTimeField(null=True, blank=True)
    queued_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True, db_index=True)
    duration = models.FloatField(null=True, blank=True)
    items = models.JSONField(default=list)
    error = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ['-queued_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['plan', 'scheduled_slot'],
                                    name='inspection_plan_slot_once'),
            models.UniqueConstraint(fields=['plan'], condition=models.Q(
                phase__in=['queued', 'running']), name='inspection_plan_active_once'),
            models.UniqueConstraint(fields=['phase'], condition=models.Q(phase='running'),
                                    name='inspection_single_running'),
        ]