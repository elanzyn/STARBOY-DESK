from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta

from apps.authentication.models import User
from apps.notifications.models import Notification
from apps.tickets.models import Ticket, TicketStatusLog


@login_required
def dashboard(request):
    now = timezone.now()
    ticket_qs = Ticket.objects.all()

    # Basic counts
    opened = ticket_qs.filter(status=Ticket.Status.OPEN).count()
    progress = ticket_qs.filter(status=Ticket.Status.IN_PROGRESS).count()
    resolved = ticket_qs.filter(status=Ticket.Status.RESOLVED).count()
    closed = ticket_qs.filter(status=Ticket.Status.CLOSED).count()

    # Resolved today
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    resolved_today = ticket_qs.filter(status=Ticket.Status.RESOLVED, resolved_at__gte=start_of_day).count()

    # Overdue tickets (past SLA target)
    # Simpler calculation: by comparing created_at + sla_target_hours per ticket (safe for SQLite/dev)
    overdue = [t for t in ticket_qs if t.is_open and (t.created_at + timedelta(hours=t.sla_target_hours)) < now]
    overdue_count = len(overdue)

    # Resolution rate
    total_closed_or_resolved = ticket_qs.filter(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED]).count()
    total = ticket_qs.count() or 1
    resolution_rate = round((total_closed_or_resolved / total) * 100, 2)

    # Top admins by resolved in last 7 days
    week_ago = now - timedelta(days=7)
    top_admins = (
        User.objects.filter(cargo=User.Cargo.ADMIN)
        .annotate(resolved_count=Count('assigned_tickets', filter=Q(assigned_tickets__resolved_at__gte=week_ago)))
        .order_by('-resolved_count')[:5]
    )

    # Average first response time (minutes)
    answered = ticket_qs.filter(first_response_at__isnull=False)
    avg_response = None
    if answered.exists():
        total_minutes = sum([ (t.first_response_at - t.created_at).total_seconds() for t in answered ])
        avg_response = round((total_minutes / 60) / answered.count(), 2)

    # Tickets by priority
    by_priority = ticket_qs.values('priority').annotate(count=Count('id'))

    # Tickets per day (last 14 days)
    days = 14
    labels = []
    series = []
    for i in range(days, 0, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        labels.append(day_start.strftime('%d/%m'))
        series.append(ticket_qs.filter(created_at__gte=day_start, created_at__lt=day_end).count())

    context = {
        'opened': opened,
        'in_progress': progress,
        'resolved': resolved,
        'closed': closed,
        'resolved_today': resolved_today,
        'overdue_count': overdue_count,
        'resolution_rate': resolution_rate,
        'top_admins': top_admins,
        'avg_response_minutes': avg_response,
        'by_priority': list(by_priority),
        'tickets_per_day_labels': labels,
        'tickets_per_day_series': series,
        'page_title': 'Analytics',
    }
    return render(request, 'analytics/dashboard.html', context)
