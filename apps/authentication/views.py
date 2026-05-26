from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.encoding import force_str
from .forms import LoginForm, RegisterForm, PasswordResetRequestForm
from .models import User, PasswordResetRequest
from .services import create_password_reset_request
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic.edit import FormView


def login_view(request):
    if request.user.is_authenticated:
        if not request.user.has_active_plan():
            return redirect('authentication:plan_selection')
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        # If form invalid show friendly message
        if not form.is_valid():
            messages.error(request, _('Preencha todos os campos.'))
        else:
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember')
            user = authenticate(request, email=email, password=password)
            # If authentication succeeded
            if user is not None:
                if not user.is_active:
                    messages.error(request, _('Conta desativada.'))
                else:
                    login(request, user)
                    if not remember:
                        request.session.set_expiry(0)
                    messages.success(request, _('Login realizado com sucesso!'))
                    if not user.has_active_plan():
                        return redirect('authentication:plan_selection')
                    return redirect('dashboard:home')
            else:
                # user could be invalid credentials or inactive — check existence
                existing = User.objects.filter(email__iexact=email).first()
                if existing and not existing.check_password(password):
                    messages.error(request, _('Email ou senha inválidos.'))
                elif existing and not existing.is_active:
                    messages.error(request, _('Conta desativada.'))
                else:
                    messages.error(request, _('Email ou senha inválidos.'))
    else:
        form = LoginForm()
    return render(request, 'authentication/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        if not request.user.has_active_plan():
            return redirect('authentication:plan_selection')
        return redirect('dashboard:home')
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        available_plans = {plan['id'] for plan in _plan_catalog()}
        if plan_id not in available_plans:
            messages.error(request, _('Selecione um plano válido.'))
            return redirect('authentication:plan_selection')
        form = RegisterForm(request.POST)
        selected_plan = _get_plan(plan_id)
        if form.is_valid():
            user = form.save()
            expires_at = timezone.now() + timedelta(days=60)
            user.plan_id = plan_id
            user.plan_status = User.PlanStatus.TRIALING
            user.plan_expires_at = expires_at
            user.save(update_fields=['plan_id', 'plan_status', 'plan_expires_at'])
            request.session['plan_confirm'] = {
                'plan_label': force_str(dict(User.Plan.choices).get(plan_id, plan_id)),
                'expires_at': expires_at.strftime('%d/%m/%Y'),
                'email': user.email,
            }
            return redirect('authentication:plan_confirm')
    else:
        plan_id = request.GET.get('plan')
        selected_plan = _get_plan(plan_id)
        if not selected_plan:
            messages.info(request, _('Escolha um plano antes de criar a conta.'))
            return redirect('authentication:plan_selection')
        form = RegisterForm()
    return render(request, 'authentication/register.html', {'form': form, 'selected_plan': selected_plan})


def logout_view(request):
    logout(request)
    messages.success(request, _('Logout realizado com sucesso!'))
    return redirect('authentication:login')


def forgot_password_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()
            if user:
                reset_request = create_password_reset_request(user)
                messages.success(request, _('Solicitação enviada. Aguarde aprovação do superadmin.'))
                return redirect('authentication:forgot_password')
            messages.error(request, _('Nenhuma conta encontrada para este email.'))
    else:
        form = PasswordResetRequestForm()
    return render(request, 'authentication/forgot_password.html', {'form': form})


def _plan_catalog():
    return [
        {
            'id': User.Plan.MONTHLY,
            'title': 'Plano Mensal',
            'price': 'R$ 99,99',
            'period': 'mês',
            'badge': '2 meses grátis',
            'billing': 'Após 2 meses grátis',
        },
        {
            'id': User.Plan.SEMIANNUAL,
            'title': 'Plano Semestral',
            'price': 'R$ 84,99',
            'period': 'mês',
            'badge': '15% de desconto',
            'billing': 'Cobrado semestralmente',
        },
        {
            'id': User.Plan.ANNUAL,
            'title': 'Plano Anual',
            'price': 'R$ 74,99',
            'period': 'mês',
            'badge': '25% de desconto',
            'billing': 'Cobrado anualmente',
        },
    ]


def _get_plan(plan_id):
    if not plan_id:
        return None
    for plan in _plan_catalog():
        if plan['id'] == plan_id:
            return plan
    return None


def plan_selection_view(request):
    if request.user.is_authenticated and request.user.has_active_plan():
        return redirect('dashboard:home')
    return render(request, 'authentication/plan_selection.html', {
        'plans': _plan_catalog(),
        'page_title': 'Escolha seu plano',
    })


@login_required
@require_POST
def plan_activate_view(request):
    if request.user.has_active_plan():
        return redirect('dashboard:home')
    plan_id = request.POST.get('plan_id')
    available_plans = {plan['id'] for plan in _plan_catalog()}
    if plan_id not in available_plans:
        messages.error(request, _('Plano inválido.'))
        return redirect('authentication:plan_selection')

    # TODO: Integrar API de Pagamento Real aqui (cartão/PIX/assinatura)
    request.user.plan_id = plan_id
    request.user.plan_status = User.PlanStatus.TRIALING
    request.user.plan_expires_at = timezone.now() + timedelta(days=60)
    request.user.save(update_fields=['plan_id', 'plan_status', 'plan_expires_at'])
    request.session['plan_confirm'] = {
        'plan_label': force_str(dict(User.Plan.choices).get(plan_id, plan_id)),
        'expires_at': request.user.plan_expires_at.strftime('%d/%m/%Y'),
        'email': request.user.email,
    }
    return redirect('authentication:plan_confirm')


def plan_confirm_view(request):
    plan_label = ''
    expires_at = ''
    email = ''
    if request.user.is_authenticated and request.user.has_active_plan():
        plan_label = force_str(dict(User.Plan.choices).get(request.user.plan_id, ''))
        expires_at = request.user.plan_expires_at.strftime('%d/%m/%Y') if request.user.plan_expires_at else ''
        email = request.user.email
    else:
        confirm_data = request.session.pop('plan_confirm', None)
        if not confirm_data:
            return redirect('authentication:plan_selection')
        plan_label = confirm_data.get('plan_label', '')
        expires_at = confirm_data.get('expires_at', '')
        email = confirm_data.get('email', '')
    return render(request, 'authentication/plan_confirm.html', {
        'plan_label': plan_label,
        'plan_expires_at': expires_at,
        'plan_email': email,
        'page_title': 'Plano ativado',
    })


class TailwindSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20'
        self.fields['new_password1'].widget.attrs.update({
            'class': base_classes,
            'placeholder': 'Crie uma senha segura',
            'id': 'id_password1',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': base_classes,
            'placeholder': 'Repita a senha',
            'id': 'id_password2',
        })


class ResetPasswordConfirmTokenView(PasswordResetConfirmView):
    template_name = 'authentication/reset_password.html'
    form_class = TailwindSetPasswordForm
    success_url = reverse_lazy('authentication:login')

    def dispatch(self, request, *args, **kwargs):
        token = kwargs.get('token')
        try:
            self.reset_request = PasswordResetRequest.objects.select_related('user').get(token=token)
        except PasswordResetRequest.DoesNotExist:
            messages.error(request, _('Token inválido.'))
            return redirect('authentication:login')
        if self.reset_request.status != PasswordResetRequest.Status.APROVADO:
            messages.error(request, _('Solicitação não aprovada.'))
            return redirect('authentication:login')
        if self.reset_request.expira_em < timezone.now():
            messages.error(request, _('Token expirado.'))
            return redirect('authentication:login')
        self.user = self.reset_request.user
        self.validlink = True
        return FormView.dispatch(self, request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        form.save()
        self.reset_request.status = PasswordResetRequest.Status.RECUSADO
        self.reset_request.save(update_fields=['status'])
        messages.success(self.request, _('Senha redefinida com sucesso.'))
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_request'] = self.reset_request
        return context
