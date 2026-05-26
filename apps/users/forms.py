from django import forms
from apps.authentication.models import User
from apps.authentication.validators import validate_full_name


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('nome_completo', 'username', 'email', 'bio', 'telefone')
        widgets = {
            'nome_completo': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            }),
            'username': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
            }),
        }

    def clean_nome_completo(self):
        nome = self.cleaned_data.get('nome_completo', '')
        return validate_full_name(nome)
