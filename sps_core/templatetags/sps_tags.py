from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def status_badge(status):
    """Возвращение HTML бейдж статуса."""
    badges = {
        'running': ('🟢', 'green', 'РАБОТАЕТ'),
        'warning': ('🟡', 'yellow', 'ВНИМАНИЕ'),
        'error': ('🔴', 'red', 'ПРОБЛЕМА'),
        'inactive': ('⚪', 'gray', 'НЕАКТИВНА'),
        'maintenance': ('🟠', 'orange', 'ОБСЛУЖИВАНИЕ'),
    }

    icon, color, text = badges.get(status, ('⚪', 'gray', 'НЕИЗВЕСТНО'))

    return mark_safe(
        str.format(
            '<span class="badge badge-{}">{} {}</span>',
            color, icon, text)
    )

@register.simple_tag
def progress_bar(current, total, width=100):
    """Прогресс-бар для ресурса запчасти."""
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100

    if percentage >= 90:
        color = 'red'
    elif percentage >= 70:
        color = 'yellow'
    else:
        color = 'green'

    return mark_safe(
        str.format(
            '<div class="progress-bar" style="width: {}%;">'
            '<span class="progress-text {}">{}%</span>'
            '</div>',
            width, color, int(percentage)
        )
    )

@register.filter
def multiply(value, arg):
    """Умножение для шаблонов."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def hours_to_days(hours):
    """Конвертация часов в дни."""
    try:
        days = int(hours / 24)
        return f'{days:.1f} дн.'
    except (ValueError, TypeError):
        return '-'
