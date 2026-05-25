from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db.models import Q

from apps.authentication.decorators import superadmin_required
from apps.authentication.models import PasswordResetRequest, User
from apps.authentication.services import approve_password_reset_request, reject_password_reset_request, create_password_reset_request
from apps.notifications.models import Notification
from apps.tickets.models import TicketStatusLog
from django.utils import timezone


@superadmin_required
def dashboard(request):
    return render(
        request,
        'superadmin/dashboard.html',
        {
            'page_title': 'Painel Admin',
            'users_count': User.objects.count(),
            'admins_count': User.objects.filter(cargo=User.Cargo.ADMIN, is_active=True).count(),
            'resets_count': PasswordResetRequest.objects.count(),
        },
    )


@superadmin_required
def users(request):
    q = request.GET.get('q', '').strip()
    pending_resets = PasswordResetRequest.objects.filter(status=PasswordResetRequest.Status.PENDENTE).select_related('user').order_by('-solicitado_em')
    users_qs = User.objects.all().order_by('-criado_em')
    if q:
        users_qs = users_qs.filter(
            Q(telefone__icontains=q) | Q(email__icontains=q) | Q(nome_completo__icontains=q) | Q(username__icontains=q)
        )
    return render(request, 'superadmin/users.html', {
        'page_title': 'Gerenciar usuários', 
        'users': users_qs,
        'pending_resets': pending_resets,
        'q': q,
    })


@superadmin_required
@require_POST
def toggle_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('superadmin:users')


@superadmin_required
@require_POST
def request_user_password_reset(request, user_id):
    user = get_object_or_404(User, id=user_id)
    # Criar nova solicitação de reset (sobrescreve qualquer anterior pendente)
    PasswordResetRequest.objects.filter(user=user, status=PasswordResetRequest.Status.PENDENTE).delete()
    create_password_reset_request(user)
    return redirect('superadmin:users')


@superadmin_required
def logs(request):
    # Filters from GET
    typ = request.GET.get('type', 'all')  # 'all' | 'ticket' | 'password_reset' | 'notification'
    start = request.GET.get('start')  # expected YYYY-MM-DD
    end = request.GET.get('end')

    timeline = []

    # Helper to parse dates
    from datetime import datetime
    def parse_date(d):
        try:
            return datetime.strptime(d, '%Y-%m-%d').date()
        except Exception:
            return None

    start_date = parse_date(start)
    end_date = parse_date(end)

    # Ticket status logs
    if typ in ('all', 'ticket'):
        qs = TicketStatusLog.objects.select_related('changed_by', 'ticket').all()
        if start_date:
            qs = qs.filter(changed_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(changed_at__date__lte=end_date)
        for log in qs:
            timeline.append({
                'time': log.changed_at,
                'type': 'ticket_status',
                'summary': f'Chamado #{log.ticket.id}: {log.old_status} → {log.new_status}',
                'actor': log.changed_by.nome_completo if log.changed_by else 'Sistema',
                'meta': {
                    'ticket_id': log.ticket.id,
                    'duration': log.duration_human() if getattr(log, 'duration_human', None) else None,
                }
            })

    # Password reset requests
    if typ in ('all', 'password_reset'):
        qs = PasswordResetRequest.objects.select_related('user', 'aprovado_por').all()
        if start_date:
            qs = qs.filter(solicitado_em__date__gte=start_date)
        if end_date:
            qs = qs.filter(solicitado_em__date__lte=end_date)
        for r in qs:
            timeline.append({
                'time': r.solicitado_em,
                'type': 'password_reset',
                'summary': f'Reset de senha para {r.user.email} — {r.get_status_display()}',
                'actor': r.aprovado_por.nome_completo if r.aprovado_por else 'Sistema',
                'meta': {
                    'user_id': r.user.id,
                    'status': r.status,
                }
            })

    # Notifications (recent)
    if typ in ('all', 'notification'):
        qs = Notification.objects.select_related('user').all()
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        for n in qs:
            timeline.append({
                'time': n.created_at,
                'type': 'notification',
                'summary': f'Notificação para {n.user.email}: {n.title}',
                'actor': n.user.nome_completo or n.user.email,
                'meta': {
                    'category': n.category,
                }
            })

    # sort by time desc and limit
    timeline_sorted = sorted(timeline, key=lambda x: x['time'], reverse=True)[:200]

    return render(request, 'superadmin/logs.html', {
        'page_title': 'Logs',
        'timeline': timeline_sorted,
        'filter_type': typ,
        'filter_start': start_date,
        'filter_end': end_date,
    })


@superadmin_required
def password_resets(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        reset_id = request.POST.get('reset_id')
        reset = get_object_or_404(PasswordResetRequest, id=reset_id)
        if action == 'approve':
            approve_password_reset_request(reset, request.user)
        elif action == 'reject':
            reject_password_reset_request(reset, request.user)
        return redirect('superadmin:password_resets')

    resets = PasswordResetRequest.objects.select_related('user', 'aprovado_por').order_by('-solicitado_em')[:20]
    return render(request, 'superadmin/password_resets.html', {'page_title': 'Solicitações reset', 'resets': resets})
