# sps_events/models.py

from django.db import models
from django.contrib.auth.models import User

from sps_lines.models import Line, Node, Sensor

from sps_events.enums import Severity, SeverityColor, EventType


class Event(models.Model):
    """Журнал событий производственной линии."""

    # Типы событий.
    EVENT_TYPE_CHOICES = [
        (EventType.status_change.name, EventType.status_change.value),
        (EventType.node_error.name, EventType.node_error.value),
        (EventType.sensor_alert.name, EventType.sensor_alert.value),
        (EventType.maintenance.name, EventType.maintenance.value),
        (EventType.part_replace.name, EventType.part_replace.value),
        (EventType.manual.name, EventType.manual.value),
        (EventType.system.name, EventType.system.value),
    ]

    SEVERITY_CHOICES = [
        (Severity.info.name, Severity.info.value),
        (Severity.success.name, Severity.success.value),
        (Severity.warning.name, Severity.warning.value),
        (Severity.error.name, Severity.error.value),
        (Severity.critical.name, Severity.critical.value),
    ]

    # Связи.
    line = models.ForeignKey(
        Line, on_delete=models.CASCADE,
        verbose_name='Линия', related_name='events'
    )
    node = models.ForeignKey(
        Node, on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='Узел', related_name='events'
    )
    sensor = models.ForeignKey(
        Sensor, on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='Сенсор', related_name='events'
    )

    # Датчик события.
    event_type = models.CharField(
        max_length=50, choices=EVENT_TYPE_CHOICES,
        default=EventType.status_change.name,
        verbose_name='Тип события'
    )
    severity = models.CharField(
        max_length=50, choices=SEVERITY_CHOICES,
        default=Severity.info.name,
        verbose_name='Важность'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Сообщение'
    )

    # Метаданные.
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время события'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Пользователь',
        help_text='Создатель события'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Доп. данные',
        help_text='Дополнительные данные в JSON формате'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Событие',
        verbose_name_plural = 'События'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['line', '-created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['severity'])
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title} — {self.line.name}"

    @property
    def severity_color(self):
        """Цвет для отображения."""
        colors = {
            SeverityColor.info.name: SeverityColor.info.value,
            SeverityColor.success.name: SeverityColor.success.value,
            SeverityColor.warning.name: SeverityColor.warning.value,
            SeverityColor.error.name: SeverityColor.error.value,
            SeverityColor.critical.name: SeverityColor.critical.value,
        }
        return colors.get(self.severity, SeverityColor.info.value)
