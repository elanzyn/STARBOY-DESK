from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, RegisterForm, PasswordResetRequestForm, PasswordResetForm
from .models import User, PasswordResetRequest
from .services import create_password_reset_request, apply_password_reset_token
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def login_view(request):
    if request.user.is_authenticated:
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
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _('Conta criada com sucesso! Faça login.'))
            return redirect('authentication:login')
    else:
        form = RegisterForm()
    return render(request, 'authentication/register.html', {'form': form})


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


def reset_password_view(request, token):
    try:
        reset_request = PasswordResetRequest.objects.select_related('user').get(token=token)
    except PasswordResetRequest.DoesNotExist:
        messages.error(request, _('Token inválido.'))
        return redirect('authentication:login')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            try:
                apply_password_reset_token(token, form.cleaned_data['password1'])
                messages.success(request, _('Senha redefinida com sucesso.'))
                return redirect('authentication:login')
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = PasswordResetForm()

    return render(request, 'authentication/reset_password.html', {'form': form, 'reset_request': reset_request})
