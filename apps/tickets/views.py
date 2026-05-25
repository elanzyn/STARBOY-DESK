from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django import forms
from django.db.models import Q, Exists, OuterRef
from django.core.paginator import Paginator

from apps.authentication.models import User
from apps.notifications.models import Notification
from .forms import TicketForm
from .models import Ticket, TicketStatusLog
from django.conf import settings


@login_required
def ticket_list(request):
    # base queryset depending on role
    if request.user.cargo == User.Cargo.SUPER_ADMIN:
        tickets = Ticket.objects.all()
    elif request.user.cargo == User.Cargo.ADMIN:
        # Admins should see all tickets so they can close requests from any requester
        tickets = Ticket.objects.all()
    else:
        tickets = Ticket.objects.filter(Q(requester=request.user) | Q(assignee=request.user))

    # optional filter parameter (e.g. ?filter=awaiting_close)
    active_filter = request.GET.get('filter')
    if active_filter == 'awaiting_close':
        tickets = tickets.filter(status_logs__new_status='REQUESTER_CONFIRMED').distinct()

    # annotate whether requester has already confirmed resolution
    try:
        tickets = tickets.annotate(requester_confirmed=Exists(TicketStatusLog.objects.filter(ticket=OuterRef('pk'), new_status='REQUESTER_CONFIRMED')))
    except Exception:
        # fall back silently if DB doesn't support Exists for some reason
        pass

    # paginate
    try:
        page_num = int(request.GET.get('page', 1))
    except Exception:
        page_num = 1
    paginator = Paginator(tickets, 10)
    try:
        tickets_page = paginator.get_page(page_num)
    except Exception:
        tickets_page = paginator.get_page(1)

    return render(request, 'tickets/list.html', {'tickets': tickets_page, 'page_obj': tickets_page, 'paginator': paginator, 'page_number': tickets_page.number, 'page_title': 'Tickets', 'active_filter': active_filter, 'tickets_enable_requester_close': settings.TICKETS_ENABLE_REQUESTER_CLOSE})


@login_required
def ticket_create(request):
    # Allow admins/superadmin to create tickets on behalf of other users via requester_id
    users_for_select = None
    if request.user.cargo in {User.Cargo.ADMIN, User.Cargo.SUPER_ADMIN}:
        users_for_select = User.objects.filter(is_active=True).order_by('nome_completo')

    if request.method == 'POST':
        form = TicketForm(request.POST)
        # if admin, add assignee field to form so it binds/validates from POST
        if users_for_select:
            form.fields['assignee'] = forms.ModelChoiceField(
                queryset=users_for_select,
                required=False,
                widget=forms.Select(attrs={
                    'class': 'w-full rounded-2xl border border-white/6 px-4 py-3 text-slate-100',
                    'data-custom-select': 'true',
                    'style': 'background-color: rgba(15,23,42,0.95) !important; color: #e6eef8 !important;'
                })
            )
        if form.is_valid():
            # If admin/superadmin is creating the ticket they must choose a requester
            if users_for_select and not request.POST.get('requester_id'):
                form.add_error(None, 'Selecione um solicitante ao criar o chamado (obrigatório para administradores).')
            else:
                ticket = form.save(commit=False)
                # determine requester: if admin provided requester_id use that, otherwise current user
                if request.user.cargo in {User.Cargo.ADMIN, User.Cargo.SUPER_ADMIN} and request.POST.get('requester_id'):
                    try:
                        requester_user = User.objects.get(pk=int(request.POST.get('requester_id')))
                    except Exception:
                        requester_user = request.user
                    ticket.requester = requester_user
                else:
                    ticket.requester = request.user

                # set assignee if provided (form field or POST fallback)
                assignee_obj = None
                try:
                    if hasattr(form, 'cleaned_data') and form.cleaned_data.get('assignee'):
                        assignee_obj = form.cleaned_data.get('assignee')
                    elif request.POST.get('assignee'):
                        try:
                            assignee_obj = User.objects.get(pk=int(request.POST.get('assignee')))
                        except Exception:
                            assignee_obj = None
                    if assignee_obj:
                        ticket.assignee = assignee_obj
                except Exception:
                    assignee_obj = None

                ticket.save()

                # notify the ticket requester (not the creator necessarily)
                try:
                    Notification.objects.create(
                        user=ticket.requester,
                        title='Chamado criado',
                        message=f'O chamado "{ticket.title}" foi criado com sucesso.',
                        category=Notification.Category.SUCCESS,
                    )
                except Exception:
                    # do not block creation if notification fails
                    pass

                # notify assignee if present
                try:
                    if assignee_obj:
                        try:
                            Notification.objects.create(
                                user=assignee_obj,
                                title='Novo chamado atribuído',
                                message=f'O chamado "{ticket.title}" foi atribuído a você.',
                                category=Notification.Category.INFO,
                            )
                        except Exception:
                            pass
                except Exception:
                    pass

                return redirect('tickets:list')
    else:
        form = TicketForm()

    return render(request, 'tickets/create.html', {'page_title': 'Criar Chamado', 'form': form, 'users_for_select': users_for_select})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    # Permission: requester or assignee can view own ticket; admins/superadmin can view all
    if request.user.cargo == User.Cargo.USER and ticket.requester != request.user and ticket.assignee != request.user:
        return HttpResponseForbidden('Acesso negado')

    logs = ticket.status_logs.all()

    # Calculate duration display
    duration = None
    if ticket.resolved_at:
        delta = ticket.resolved_at - ticket.created_at
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            duration = f"{total_seconds}s"
        elif total_seconds < 3600:
            duration = f"{total_seconds//60}m"
        elif total_seconds < 86400:
            duration = f"{total_seconds//3600}h {(total_seconds//60)%60}m"
        else:
            duration = f"{total_seconds//86400}d {(total_seconds//3600)%24}h"

    requester_confirmed = ticket.status_logs.filter(new_status='REQUESTER_CONFIRMED').exists()
    return render(request, 'tickets/detail.html', {
        'ticket': ticket,
        'logs': logs,
        'duration': duration,
        'page_title': ticket.title,
        'requester_confirmed': requester_confirmed,
        'tickets_enable_requester_close': settings.TICKETS_ENABLE_REQUESTER_CLOSE,
    })


@login_required
def ticket_logs(request, pk):
    """Full styled log page for a ticket's status changes"""
    ticket = get_object_or_404(Ticket, pk=pk)
    # allow assignee or requester or admins to view logs
    if request.user.cargo == User.Cargo.USER and ticket.requester != request.user and ticket.assignee != request.user:
        return HttpResponseForbidden('Acesso negado')

    logs = ticket.status_logs.select_related('changed_by').all()
    return render(request, 'tickets/logs.html', {
        'ticket': ticket,
        'logs': logs,
        'page_title': f'Histórico — {ticket.title}',
    })


@login_required
@require_POST
def ticket_change_status(request, pk):
    import logging
    logger = logging.getLogger(__name__)
    ticket = get_object_or_404(Ticket, pk=pk)
    new_status = request.POST.get('status')
    # validate status
    if new_status not in dict(Ticket.Status.choices).keys():
        return JsonResponse({'error': 'invalid_status', 'message': 'Status inválido.'}, status=400)

    # permission logic: admins can change any status; assignee can set IN_PROGRESS or RESOLVED
    allowed = False
    if request.user.cargo in {User.Cargo.ADMIN, User.Cargo.SUPER_ADMIN}:
        allowed = True
    elif ticket.assignee and ticket.assignee.pk == request.user.pk and new_status in {Ticket.Status.IN_PROGRESS, Ticket.Status.RESOLVED}:
        allowed = True

    if not allowed:
        return JsonResponse({'error': 'permission_denied', 'message': 'Você não tem permissão para alterar para esse status.'}, status=403)

    try:
        logger.debug('ticket_change_status called by %s data=%s', getattr(request.user, 'pk', None), dict(request.POST))
        # perform change
        ticket.change_status(new_status, changed_by=request.user)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.exception('Error changing ticket status: %s\n%s', e, tb)
        return JsonResponse({'error': 'internal_error', 'message': f'Erro interno ao alterar status: {str(e)}'}, status=500)

    # try to create notification, but do NOT fail the request if notification creation fails
    try:
        Notification.objects.create(
            user=ticket.requester,
            title='Status atualizado',
            message=f'O chamado "{ticket.title}" agora está {ticket.get_status_display()}.',
            category=Notification.Category.INFO,
        )
    except Exception as nerr:
        logger.exception('Failed to create notification after status change: %s', nerr)

    # return updated info
    latest_log = ticket.status_logs.first()
    duration_human = latest_log.duration_human() if latest_log and latest_log.duration_seconds else None
    return JsonResponse({
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'changed_at': latest_log.changed_at.isoformat() if latest_log else None,
        'changed_by': latest_log.changed_by.email if latest_log and latest_log.changed_by else None,
        'duration': duration_human,
    })


@login_required
@require_POST
def ticket_assign_self(request, pk):
    """Assign the current user as assignee for the ticket."""
    import logging
    logger = logging.getLogger(__name__)
    ticket = get_object_or_404(Ticket, pk=pk)
    # if already assigned to this user
    if ticket.assignee and ticket.assignee.pk == request.user.pk:
        return JsonResponse({'error': 'already_assigned', 'message': 'Você já está atribuído a este chamado.'}, status=400)
    # assign
    ticket.assignee = request.user
    ticket.save()
    try:
        Notification.objects.create(
            user=ticket.requester,
            title='Chamado atribuído',
            message=f'O chamado "{ticket.title}" foi atribuído a {request.user.nome_completo}.',
            category=Notification.Category.INFO,
        )
    except Exception:
        logger.exception('Failed to notify requester after self-assign')
    return JsonResponse({'success': True, 'assignee': request.user.nome_completo or request.user.email})


@login_required
@require_POST
def ticket_confirm_resolution(request, pk):
    """Requester confirms resolution; creates a log entry and notifies admins to close."""
    import logging
    logger = logging.getLogger(__name__)
    ticket = get_object_or_404(Ticket, pk=pk)
    # check feature flag
    if not settings.TICKETS_ENABLE_REQUESTER_CLOSE:
        return JsonResponse({'error': 'disabled', 'message': 'Funcionalidade desativada.'}, status=404)
    # only requester may confirm
    if ticket.requester.pk != request.user.pk:
        return JsonResponse({'error': 'permission_denied', 'message': 'Somente o solicitante pode confirmar a resolução.'}, status=403)
    # must be in RESOLVED state
    if ticket.status != Ticket.Status.RESOLVED:
        return JsonResponse({'error': 'invalid_state', 'message': 'Somente chamados em estado "Resolvido" podem ser confirmados.'}, status=400)
    # check if already confirmed by requester
    if ticket.status_logs.filter(new_status='REQUESTER_CONFIRMED').exists():
        return JsonResponse({'error': 'already_confirmed', 'message': 'A confirmação já foi enviada.'}, status=400)
    now = timezone.now()
    try:
        TicketStatusLog.objects.create(
            ticket=ticket,
            old_status='RESOLVED',
            new_status='REQUESTER_CONFIRMED',
            changed_by=request.user,
            changed_at=now,
            duration_seconds=None,
        )
    except Exception as e:
        logger.exception('Failed to create requester confirmation log: %s', e)
        return JsonResponse({'error': 'internal_error', 'message': 'Falha ao registrar confirmação.'}, status=500)

    # notify admins to close the ticket
    try:
        admins = User.objects.filter(cargo__in=[User.Cargo.ADMIN, User.Cargo.SUPER_ADMIN], is_active=True)
        for admin in admins:
            try:
                Notification.objects.create(
                    user=admin,
                    title='Fechamento solicitado',
                    message=f'O solicitante solicitou fechamento do chamado "{ticket.title}" (ID #{ticket.pk}).',
                    category=Notification.Category.INFO,
                )
            except Exception:
                logger.exception('Failed to notify admin %s', admin.pk)
    except Exception:
        logger.exception('Failed to retrieve admins for notification')

    return JsonResponse({'success': True, 'message': 'Confirmação enviada aos administradores.'})
