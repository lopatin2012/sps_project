# sps_events/utils.py

from django.utils import timezone

from sps_events.models import Event
from sps_events.enums import Severity, StatusType, EventType


def log_event(
        line,
        event_type,
        title,
        message='',
        severity=Severity.info.name,
        node=None,
        sensor=None,
        user=None,
        metadata=None
):
    """Создание события в журнале."""

    return Event.objects.create(
        line=line,
        event_type=event_type,
        title=title,
        message=message,
        node=node,
        sensor=sensor,
        severity=severity,
        user=user,
        metadata=metadata or {}
    )

def log_status_change(line, old_severity, new_severity, user=None):
    """Изменение статуса."""

    log_event(
        line=line,
        event_type=EventType.status_change.value,
        title=f'Статус изменён: {old_severity} -> {new_severity}',
        severity=new_severity,
        user=user,
        metadata={'old_status': old_severity, 'new_status': new_severity}
    )

def log_sensor_alert(sensor, user=None):
    """Выход датчика за пределы диапазона."""
    log_event(
        line=sensor.node.line,
        event_type=EventType.sensor_alert.name,
        title=f'Датчик {sensor.name} вне диапазона',
        message=f'Значение: {sensor.current_value} (норма: {sensor.min_value}-{sensor.max_value})',
        node=sensor.node,
        sensor=sensor,
        user=user,
        metadata={
            'current_value': str(sensor.current_value),
            'min_value': str(sensor.min_value),
            'max_value': str(sensor.max_value),
        }
    )
