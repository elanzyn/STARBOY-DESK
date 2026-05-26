from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from .validators import validate_full_name

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Senha'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirme a senha'), widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username', 'nome_completo', 'avatar', 'cargo')

    def clean_nome_completo(self):
        nome = self.cleaned_data.get('nome_completo', '')
        return validate_full_name(nome)

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('As senhas não coincidem.'))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'username', 'nome_completo', 'avatar', 'cargo', 'password', 'is_active', 'is_staff', 'is_superuser')

    def clean_password(self):
        return self.initial['password']

class LoginForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            'placeholder': 'voce@empresa.com',
        }),
    )
    password = forms.CharField(
        label=_('Senha'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            'placeholder': '••••••••',
        }),
    )
    remember = forms.BooleanField(label=_('Lembrar login'), required=False)

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Senha'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            'placeholder': 'Crie uma senha segura',
            'id': 'id_password1',
        }),
    )
    password2 = forms.CharField(
        label=_('Confirme a senha'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            'placeholder': 'Repita a senha',
            'id': 'id_password2',
        }),
    )

    class Meta:
        model = User
        # Remove avatar from registration (avatar will be editable in profile)
        fields = ('nome_completo', 'username', 'email')
        widgets = {
            'nome_completo': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'placeholder': 'Nome completo',
            }),
            'username': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'placeholder': 'username',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'placeholder': 'voce@empresa.com',
            }),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('As senhas não coincidem.'))
        return password2

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1

    def clean_nome_completo(self):
        nome = self.cleaned_data.get('nome_completo', '')
        return validate_full_name(nome)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Este email já está em uso.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_('Este username já está em uso.'))
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            'placeholder': 'voce@empresa.com',
        }),
    )


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label=_('Nova senha'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
        }),
    )
    password2 = forms.CharField(
        label=_('Confirmar nova senha'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
        }),
    )

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('As senhas não coincidem.'))
        return password2
