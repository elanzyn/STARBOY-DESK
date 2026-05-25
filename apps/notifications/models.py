from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Category(models.TextChoices):
        INFO = 'INFO', 'Info'
        SUCCESS = 'SUCCESS', 'Sucesso'
        WARNING = 'WARNING', 'Aviso'
        DANGER = 'DANGER', 'Erro'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=140)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.INFO)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.user_id}'
