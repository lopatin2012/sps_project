# sps_events/models.py

from django.db import models
from django.contrib.auth.models import User

from sps_lines.models import Line, Node, Sensor

from helpers.enums import EnumSeverity, EnumSeverityColor, EnumEventType


class Event(models.Model):
    """Журнал событий производственной линии."""

    # Типы событий.
    EVENT_TYPE_CHOICES = [
        (EnumEventType.status_change.name, EnumEventType.status_change.value),
        (EnumEventType.node_error.name, EnumEventType.node_error.value),
        (EnumEventType.sensor_alert.name, EnumEventType.sensor_alert.value),
        (EnumEventType.maintenance.name, EnumEventType.maintenance.value),
        (EnumEventType.part_replace.name, EnumEventType.part_replace.value),
        (EnumEventType.manual.name, EnumEventType.manual.value),
        (EnumEventType.system.name, EnumEventType.system.value),
    ]

    SEVERITY_CHOICES = [
        (EnumSeverity.info.name, EnumSeverity.info.value),
        (EnumSeverity.success.name, EnumSeverity.success.value),
        (EnumSeverity.warning.name, EnumSeverity.warning.value),
        (EnumSeverity.error.name, EnumSeverity.error.value),
        (EnumSeverity.critical.name, EnumSeverity.critical.value),
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
        default=EnumEventType.status_change.name,
        verbose_name='Тип события'
    )
    severity = models.CharField(
        max_length=50, choices=SEVERITY_CHOICES,
        default=EnumSeverity.info.name,
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
            EnumSeverityColor.info.name: EnumSeverityColor.info.value,
            EnumSeverityColor.success.name: EnumSeverityColor.success.value,
            EnumSeverityColor.warning.name: EnumSeverityColor.warning.value,
            EnumSeverityColor.error.name: EnumSeverityColor.error.value,
            EnumSeverityColor.critical.name: EnumSeverityColor.critical.value,
        }
        return colors.get(self.severity, EnumSeverityColor.info.value)
