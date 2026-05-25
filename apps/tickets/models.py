from django.conf import settings
from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Aberto'
        IN_PROGRESS = 'IN_PROGRESS', 'Em andamento'
        RESOLVED = 'RESOLVED', 'Resolvido'
        CLOSED = 'CLOSED', 'Fechado'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Baixa'
        MEDIUM = 'MEDIUM', 'Média'
        HIGH = 'HIGH', 'Alta'
        URGENT = 'URGENT', 'Urgente'

    title = models.CharField(max_length=160)
    description = models.TextField()
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_tickets')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    sla_target_hours = models.PositiveIntegerField(default=24)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.status in {self.Status.OPEN, self.Status.IN_PROGRESS}

    def change_status(self, new_status, changed_by):
        """
        Change ticket status, create a TicketStatusLog and update timestamps.
        Only call from views with permission checks.
        """
        old = self.status
        now = timezone.now()
        # Set first_response_at when moving to IN_PROGRESS if not set
        if old == self.Status.OPEN and new_status == self.Status.IN_PROGRESS and not self.first_response_at:
            self.first_response_at = now
        # Set resolved_at when moving to RESOLVED
        if new_status == self.Status.RESOLVED:
            self.resolved_at = now
        # Set closed time when moving to CLOSED
        if new_status == self.Status.CLOSED and not self.resolved_at:
            self.resolved_at = now
        self.status = new_status
        self.save()
        # Calculate duration until resolution if resolved_at set
        duration_seconds = None
        if self.resolved_at:
            duration_seconds = int((self.resolved_at - self.created_at).total_seconds())
        TicketStatusLog.objects.create(
            ticket=self,
            old_status=old,
            new_status=new_status,
            changed_by=changed_by,
            changed_at=now,
            duration_seconds=duration_seconds,
        )


class TicketStatusLog(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)
    duration_seconds = models.BigIntegerField(null=True, blank=True, help_text='Duration in seconds until resolution')

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.ticket_id} {self.old_status} -> {self.new_status} at {self.changed_at}"

    def duration_human(self):
        if not self.duration_seconds:
            return None
        secs = self.duration_seconds
        if secs < 60:
            return f"{secs}m"
        mins = secs // 60
        if mins < 60:
            return f"{mins}m"
        hours = mins // 60
        if hours < 24:
            return f"{hours}h {mins%60}m"
        days = hours // 24
        return f"{days}d {hours%24}h"
