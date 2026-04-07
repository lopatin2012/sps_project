# helpers/enums.py

from enum import Enum


class EnumSeverity(Enum):
    """Важность события"""
    info = 'Информация'
    success = 'Успех'
    warning = 'Предупреждение'
    error = 'Ошибка'
    critical = 'Критично'


class EnumSeverityColor(Enum):
    """Цвет события"""
    info = '#2563eb' # Синий. 'Информация'
    success = '#16a34a'  # Зелёный. 'Успех',
    warning = '#e0dd00' # Жёлтый. 'Предупреждение'
    error = '#dc2626' # Красный. 'Ошибка'
    critical = '#991b1b' # Тёмно-красный. 'Критично'


class EnumEventType(Enum):
    """Тип события"""
    status_change = 'Изменение статуса'
    node_error = 'Ошибка узла'
    sensor_alert = 'Оповещение датчика'
    maintenance = 'Обслуживание'
    part_replace = 'Замена запчасти'
    manual = 'Ручная запись'
    system = 'Системное'


class EnumStatusType(Enum):
    """Тип статуса"""
    no_problem = 'Нет проблем'
    warning = 'Предупреждение'
    error = 'Ошибка'
    critical = 'Критическая проблема'
    inactive = 'Не активно'
    active = 'Активно'
