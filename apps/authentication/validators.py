import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$")
PHONE_PATTERN = re.compile(r"^\d+$")


def normalize_full_name(value: str) -> str:
    return ' '.join(value.strip().split())


def validate_full_name(value: str) -> str:
    normalized = normalize_full_name(value or '')
    if not normalized:
        raise ValidationError(_('Nome completo é obrigatório.'))
    if not NAME_PATTERN.match(normalized):
        raise ValidationError(_('Nomes não podem conter números ou caracteres inválidos.'))
    return normalized


def validate_phone_number(value: str) -> str:
    normalized = (value or '').strip()
    if not normalized:
        return ''
    if not PHONE_PATTERN.match(normalized):
        raise ValidationError(_('Telefone deve conter apenas números.'))
    return normalized


def _has_sequence(value: str, min_len: int = 4) -> bool:
    text = value.lower()
    sequences = [
        'abcdefghijklmnopqrstuvwxyz',
        '0123456789',
        'qwertyuiop',
        'asdfghjkl',
        'zxcvbnm',
    ]
    for seq in sequences:
        for i in range(len(seq) - min_len + 1):
            chunk = seq[i:i + min_len]
            if chunk in text or chunk[::-1] in text:
                return True
    return False


def _has_excessive_repeat(value: str) -> bool:
    return re.search(r'(.)\1\1\1', value) is not None


def validate_strong_password(password: str) -> None:
    errors = []
    if not password:
        raise ValidationError(_('Senha é obrigatória.'))

    has_min = len(password) >= 8
    has_lower = re.search(r'[a-z]', password) is not None
    has_upper = re.search(r'[A-Z]', password) is not None
    has_digit = re.search(r'[0-9]', password) is not None
    has_symbol = re.search(r'[^A-Za-z0-9]', password) is not None

    missing = [has_min, has_lower, has_upper, has_digit, has_symbol].count(False)
    if missing >= 2:
        errors.append(_('Senha muito fraca.'))

    if not has_min:
        errors.append(_('Use no mínimo 8 caracteres.'))
    if not has_upper:
        errors.append(_('Inclua ao menos uma letra maiúscula.'))
    if not has_lower:
        errors.append(_('Inclua ao menos uma letra minúscula.'))
    if not has_digit:
        errors.append(_('Inclua ao menos um número.'))
    if not has_symbol:
        errors.append(_('Inclua ao menos um caractere especial.'))

    if _has_sequence(password):
        errors.append(_('Evite sequências simples.'))
    if _has_excessive_repeat(password):
        errors.append(_('Evite repetições excessivas.'))

    common = {
        '123456', '12345678', 'abcdef', 'qwerty', 'senha', 'password', 'admin',
        'letmein', '111111', '000000', '12345', 'qwerty123', 'senha123'
    }
    if password.lower() in common:
        errors.append(_('Senha muito fraca.'))

    if errors:
        raise ValidationError(errors)


class StrongPasswordValidator:
    def validate(self, password, user=None):
        validate_strong_password(password)

    def get_help_text(self):
        return _(
            'Use no mínimo 8 caracteres com letras maiúsculas, minúsculas, números e símbolos. '
            'Evite sequências simples e repetições.'
        )
