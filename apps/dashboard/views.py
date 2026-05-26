from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import PasswordResetRequest, User
from apps.notifications.models import Notification
from apps.tickets.models import Ticket
from django.conf import settings


def landing(request):
    return render(request, 'base/landing.html')


def _role_label(user):
    return dict(User.Cargo.choices).get(user.cargo, user.cargo)


def _default_line_data():
    labels = []
    values = []
    for offset in range(6, -1, -1):
        day = timezone.localdate() - timedelta(days=offset)
        labels.append(date_format(day, 'd/m'))
        values.append(0)
    return labels, values


def _build_ticket_series():
    labels, series = _default_line_data()
    label_to_index = {label: index for index, label in enumerate(labels)}
    daily_counts = defaultdict(int)

    since = timezone.now() - timedelta(days=7)
    for ticket in Ticket.objects.filter(created_at__gte=since):
        day_label = date_format(ticket.created_at.date(), 'd/m')
        daily_counts[day_label] += 1

    for label, value in daily_counts.items():
        if label in label_to_index:
            series[label_to_index[label]] = value

    return {
        'labels': labels,
        'datasets': [
            {
                'label': 'Tickets',
                'data': series,
                'borderColor': '#6366F1',
                'backgroundColor': 'rgba(99, 102, 241, 0.18)',
                'tension': 0.4,
                'fill': True,
            }
        ],
    }


def _build_status_series(queryset):
    status_labels = {
        Ticket.Status.OPEN: 'Abertos',
        Ticket.Status.IN_PROGRESS: 'Em andamento',
        Ticket.Status.RESOLVED: 'Resolvidos',
        Ticket.Status.CLOSED: 'Fechados',
    }
    counts = {label: 0 for label in status_labels.values()}
    for status, label in status_labels.items():
        counts[label] = queryset.filter(status=status).count()

    return {
        'labels': list(counts.keys()),
        'datasets': [
            {
                'data': list(counts.values()),
                'backgroundColor': ['#6366F1', '#14B8A6', '#22C55E', '#64748B'],
                'borderWidth': 0,
            }
        ],
    }


def _recent_ticket_rows(queryset, limit=6):
    return queryset.select_related('requester', 'assignee')[:limit]


def _build_recent_activity(user):
    activities = []
    recent_notifications = Notification.objects.filter(user=user)[:4]
    recent_resets = PasswordResetRequest.objects.filter(user=user).order_by('-solicitado_em')[:2]
    recent_tickets = Ticket.objects.filter(Q(requester=user) | Q(assignee=user)).order_by('-updated_at')[:3]

    for notification in recent_notifications:
        activities.append({
            'title': notification.title,
            'message': notification.message,
            'meta': notification.get_category_display(),
        })
    for reset_request in recent_resets:
        activities.append({
            'title': _('Solicitação de senha'),
            'message': reset_request.get_status_display(),
            'meta': reset_request.solicitado_em.strftime('%d/%m/%Y %H:%M'),
        })
    for ticket in recent_tickets:
        activities.append({
            'title': ticket.title,
            'message': ticket.get_status_display(),
            'meta': ticket.updated_at.strftime('%d/%m/%Y %H:%M'),
        })

    return activities[:6]


@login_required
def home(request):
    user = request.user
    if not user.has_active_plan():
        return redirect('authentication:plan_selection')
    tickets_qs = Ticket.objects.all()

    # handle search query
    q = request.GET.get('q', '').strip()
    search_query = None
    search_tickets = []
    search_users = []
    if q:
        search_query = q
        q_filter = Q(title__icontains=q) | Q(description__icontains=q) | Q(requester__email__icontains=q) | Q(assignee__email__icontains=q)
        if q.isdigit():
            try:
                q_id = int(q)
                q_filter = q_filter | Q(id=q_id)
            except ValueError:
                pass
        search_tickets = list(Ticket.objects.filter(q_filter).select_related('requester')[:20])
        # search users
        search_users = list(User.objects.filter(Q(nome_completo__icontains=q) | Q(email__icontains=q) | Q(username__icontains=q))[:20])

    open_tickets = tickets_qs.filter(status__in=[Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS])
    resolved_tickets = tickets_qs.filter(status=Ticket.Status.RESOLVED)
    average_sla = tickets_qs.aggregate(avg=Avg('sla_target_hours'))['avg'] or 0
    response_minutes = []
    for ticket in tickets_qs.exclude(first_response_at=None).only('created_at', 'first_response_at'):
        response_minutes.append((ticket.first_response_at - ticket.created_at).total_seconds() / 60)
    average_response = round(sum(response_minutes) / len(response_minutes)) if response_minutes else None

    # count of tickets where requester requested closure
    try:
        awaiting_close_count = Ticket.objects.filter(status_logs__new_status='REQUESTER_CONFIRMED').distinct().count()
    except Exception:
        awaiting_close_count = 0

    common_stats = [
        {
            'label': 'Tickets abertos',
            'value': open_tickets.count(),
            'icon': 'ticket',
        },
        {
            'label': 'Tickets resolvidos',
            'value': resolved_tickets.count(),
            'icon': 'check',
        },
        {
            'label': 'Fechamento solicitado',
            'value': awaiting_close_count,
            'icon': 'alert',
        },
        {
            'label': 'SLA médio',
            'value': f'{average_sla:.0f}h' if average_sla else '—',
            'icon': 'clock',
        },
        {
            'label': 'Tempo médio resposta',
            'value': f'{average_response}min' if average_response is not None else '—',
            'icon': 'bolt',
        },
    ]

    role_stats = []
    if user.cargo == User.Cargo.SUPER_ADMIN:
        role_stats = [
            {'label': 'Total de usuários', 'value': User.objects.count(), 'icon': 'users'},
            {'label': 'Admins ativos', 'value': User.objects.filter(cargo=User.Cargo.ADMIN, is_active=True).count(), 'icon': 'shield'},
            {'label': 'Solicitações pendentes', 'value': PasswordResetRequest.objects.filter(status=PasswordResetRequest.Status.PENDENTE).count(), 'icon': 'inbox'},
            {'label': 'Notificações não lidas', 'value': Notification.objects.filter(is_read=False).count(), 'icon': 'bell'},
        ]
    elif user.cargo == User.Cargo.ADMIN:
        role_stats = [
            {'label': 'Tickets atribuídos', 'value': tickets_qs.filter(assignee=user).count(), 'icon': 'ticket'},
            {'label': 'Tickets resolvidos', 'value': tickets_qs.filter(assignee=user, status=Ticket.Status.RESOLVED).count(), 'icon': 'check'},
            {'label': 'SLA pessoal', 'value': f'{average_sla:.0f}h' if average_sla else '—', 'icon': 'clock'},
            {'label': 'Comentários recentes', 'value': Notification.objects.filter(user=user).count(), 'icon': 'chat'},
        ]
    else:
        role_stats = [
            {'label': 'Meus tickets', 'value': tickets_qs.filter(requester=user).count(), 'icon': 'ticket'},
            {'label': 'Tickets abertos', 'value': tickets_qs.filter(requester=user, status__in=[Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS]).count(), 'icon': 'clock'},
            {'label': 'Respostas recentes', 'value': Notification.objects.filter(user=user).count(), 'icon': 'message'},
            {'label': 'Chamados resolvidos', 'value': tickets_qs.filter(requester=user, status=Ticket.Status.RESOLVED).count(), 'icon': 'check'},
        ]

    recent_tickets = _recent_ticket_rows(
        tickets_qs.filter(Q(requester=user) | Q(assignee=user)) if user.cargo != User.Cargo.SUPER_ADMIN else tickets_qs
    )

    return render(
        request,
        'dashboard/home.html',
        {
            'role_label': _role_label(user),
            'common_stats': common_stats,
            'role_stats': role_stats,
            'tickets_count': tickets_qs.count(),
            'tickets_open_count': open_tickets.count(),
            'tickets_resolved_count': resolved_tickets.count(),
            'tickets_chart': _build_ticket_series(),
            'status_chart': _build_status_series(tickets_qs),
            'activities': _build_recent_activity(user),
            'recent_tickets': recent_tickets,
            'pending_resets': PasswordResetRequest.objects.filter(status=PasswordResetRequest.Status.PENDENTE).order_by('-solicitado_em')[:5],
            'recent_notifications': Notification.objects.filter(user=user).order_by('-created_at')[:5],
            'page_title': _('Dashboard'),
                        'search_query': search_query,
                        'search_tickets': search_tickets,
                        'search_users': search_users,
                                    'tickets_enable_requester_close': settings.TICKETS_ENABLE_REQUESTER_CLOSE,
                                },
                            )


@login_required
def export_dashboard_csv(request):
    import csv
    from django.http import HttpResponse
    
    user = request.user
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="starboy-dashboard-relatorio-{timezone.now().strftime("%d-%m-%Y")}.csv"'
    
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    # Cabeçalho
    writer.writerow(['STARBOY DESK - RELATÓRIO DO DASHBOARD'])
    writer.writerow([f'Gerado em: {timezone.now().strftime("%d/%m/%Y às %H:%M:%S")}'])
    writer.writerow([f'Usuário: {user.nome_completo} ({user.email})'])
    writer.writerow([])
    
    # Tickets
    writer.writerow(['CHAMADOS'])
    writer.writerow(['ID', 'Título', 'Status', 'Prioridade', 'Solicitante', 'Atualizado em'])
    tickets_qs = Ticket.objects.all()
    for ticket in tickets_qs[:100]:
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.get_status_display(),
            ticket.get_priority_display(),
            ticket.requester.nome_completo if ticket.requester else '—',
            ticket.updated_at.strftime('%d/%m/%Y %H:%M'),
        ])
    
    writer.writerow([])
    writer.writerow(['RESUMO'])
    writer.writerow(['Métrica', 'Valor'])
    
    open_tickets = tickets_qs.filter(status__in=[Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS])
    resolved_tickets = tickets_qs.filter(status=Ticket.Status.RESOLVED)
    
    writer.writerow(['Total de chamados', tickets_qs.count()])
    writer.writerow(['Chamados abertos', open_tickets.count()])
    writer.writerow(['Chamados resolvidos', resolved_tickets.count()])
    writer.writerow(['Taxa de resolução', f'{(resolved_tickets.count() / tickets_qs.count() * 100):.1f}%' if tickets_qs.exists() else '0%'])
    
    if user.cargo == User.Cargo.SUPER_ADMIN:
        writer.writerow([])
        writer.writerow(['USUÁRIOS'])
        writer.writerow(['Nome', 'Email', 'Cargo', 'Status', 'Criado em'])
        for u in User.objects.all()[:100]:
            writer.writerow([
                u.nome_completo,
                u.email,
                u.get_cargo_display(),
                'Ativo' if u.is_active else 'Inativo',
                u.criado_em.strftime('%d/%m/%Y'),
            ])
    
    return response
