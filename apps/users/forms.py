from django import forms
from apps.authentication.models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('nome_completo', 'username', 'email', 'bio', 'telefone', 'avatar')
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
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'block w-full rounded-2xl border border-dashed border-white/15 bg-white/5 px-4 py-3 text-sm text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-white file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950',
            }),
        }
