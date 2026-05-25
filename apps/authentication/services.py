import secrets
from datetime import timedelta
from django.utils import timezone
from .models import PasswordResetRequest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def create_password_reset_request(user):
    token = secrets.token_urlsafe(32)
    expira_em = timezone.now() + timedelta(hours=1)
    req = PasswordResetRequest.objects.create(user=user, token=token, expira_em=expira_em)
    return req

def send_password_reset_email(user, token, request_obj=None):
    """Envia email com link completo de reset de senha"""
    # Montar a URL completa
    domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
    protocol = 'https' if not settings.DEBUG else 'http'
    reset_url = f'{protocol}://{domain}/auth/reset-password/{token}/'
    
    subject = '🔐 Redefinir Sua Senha - STARBOY DESK'
    
    # Context para o template
    context = {
        'user': user,
        'reset_url': reset_url,
        'reset_link': reset_url,
        'token': token,
        'expires_in': '1 hora',
    }
    
    # Renderizar HTML do email
    html_message = render_to_string('emails/password_reset.html', context)
    plain_message = f"""
Olá {user.nome},

Você solicitou um reset de senha no STARBOY DESK.

Clique no link abaixo para redefinir sua senha:
{reset_url}

Este link expira em 1 hora.

Se você não solicitou isso, ignore este email.

Atenciosamente,
STARBOY DESK
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Erro ao enviar email: {e}')
        return False

def approve_password_reset_request(request_obj, superadmin):
    request_obj.status = 'APROVADO'
    request_obj.aprovado_por = superadmin
    request_obj.aprovado_em = timezone.now()
    request_obj.save()
    
    # Enviar email com o link
    send_password_reset_email(request_obj.user, request_obj.token, request_obj)
    
    return request_obj


def reject_password_reset_request(request_obj, superadmin):
    request_obj.status = 'RECUSADO'
    request_obj.aprovado_por = superadmin
    request_obj.aprovado_em = timezone.now()
    request_obj.save()
    return request_obj


def apply_password_reset_token(token, new_password):
    User = get_user_model()
    request_obj = PasswordResetRequest.objects.select_related('user').get(token=token)
    if request_obj.status != PasswordResetRequest.Status.APROVADO:
        raise ValueError('Solicitação não aprovada.')
    if request_obj.expira_em < timezone.now():
        raise ValueError('Token expirado.')

    user = request_obj.user
    user.set_password(new_password)
    user.save(update_fields=['password'])
    request_obj.status = PasswordResetRequest.Status.RECUSADO
    request_obj.save(update_fields=['status'])
    return user
