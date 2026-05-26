from django import forms
from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'description', 'category', 'priority')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'placeholder': 'Resumo do chamado',
            }),
            'description': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'placeholder': 'Descreva o problema com o máximo de contexto possível',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full rounded-2xl border border-white/6 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'data-custom-select': 'true',
            }),
            'priority': forms.Select(attrs={
                            'class': 'w-full rounded-2xl border border-white/6 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/20',
                'data-custom-select': 'true',
                        }),
        }
