from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PasswordResetRequest
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=PasswordResetRequest)
def notify_superadmin_on_reset_request(sender, instance, created, **kwargs):
    if created and instance.status == 'PENDENTE':
        # Enviar notificação para superadmin
        pass  # Implementar lógica de notificação/email
