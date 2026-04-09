# sps_lines/models.py

from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Line(models.Model):
    """Производственная линия."""
    name = models.CharField(max_length=200, verbose_name='Название линии')
    inventory_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Инвентарный номер'
    )
    performance = models.IntegerField(
        verbose_name='Производительность (шт/час)',
        validators=[MinValueValidator(0)]
    )
    photo = models.ImageField(
        upload_to='photos/lines',
        blank=True,
        null=True,
        verbose_name='Фотография линии'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    datetime_commissioning = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата ввода в эксплуатацию'
    )
    datetime_decommissioning = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата вывода из эксплуатации'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    class Meta:
        ordering = ['-datetime_commissioning']
        verbose_name = 'Линия'
        verbose_name_plural = 'Линии'

    def __str__(self):
        return f"{self.name} (инв. {self.inventory_number})"

    def is_decommissioned(self):
        """Проверка, выведена ли линия из эксплуатации."""
        return self.datetime_decommissioning is not None

    def get_status(self):
        """Опдереление статуса линии на основе узлов и датчиков."""
        if not self.is_active or self.datetime_decommissioning:
            return 'inactive'

        elif self.nodes.filter(is_active=False).exists():
            return 'error'

        if self.nodes.filter(is_maintenance=True).exists():
            return 'maintenance'

        else:
            # Проверка датчиков
            for node in self.nodes.all():
                for sensor in node.sensors.all():
                    if not sensor.is_in_range:
                        return 'warning'
        return 'running'

    @property
    def sensors_count(self):
        """Получить количество датчиков на линии."""
        result = self.nodes.aggregate(total=models.Count('sensors'))
        return result['total'] or 0


class Node(models.Model):
    """Узел линии (агрегат, механизм)."""
    node_type = models.CharField(
        max_length=100,
        choices=[
            ('conveyor', 'Конвейер'),
            ('motor', 'Двигатель'),
            ('sensor_block', 'Блок датчиков'),
            ('controller', 'Контроллер'),
            ('actuator', 'Исполнительный механизм'),
            ('marking', 'Маркировка'),
            ('printer', 'Принтер'),
            ('other', 'Другое'),
        ],
        verbose_name='Тип узла'
    )
    line = models.ForeignKey(
        Line,
        on_delete=models.CASCADE,
        verbose_name='Линия',
        related_name='nodes'
    )
    name = models.CharField(max_length=200, verbose_name='Название узла')
    inventory_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Инвентарный номер узла'
    )
    photo = models.ImageField(
        upload_to='photos/nodes',
        blank=True,
        null=True,
        verbose_name='Фотография узла'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    is_maintenance = models.BooleanField(
        default=False,
        verbose_name='Обслуживание'
    )
    datetime_service = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата последнего обслуживания'
    )
    service_interval_hours = models.IntegerField(
        default=0,
        verbose_name='Интервал обслуживания (часов)',
        help_text='Рекомендуемый интервал между обслуживаниями'
    )
    # Поля для визуального расположения
    position_x = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Позиция X (%)',
        help_text='Позиция по горизонтали (0-100%)'
    )
    position_y = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Позиция Y (%)',
        help_text='Позиция по вертикали (0-100%)'
    )
    position_z = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        blank=True,
        null=True,
        verbose_name='Позиция Z (глубина)',
        help_text='Для 3D отображения'
    )

    class Meta:
        ordering = ['line', 'position_x', 'position_y']
        verbose_name = 'Узел'
        verbose_name_plural = 'Узлы'
        unique_together = ['line', 'inventory_number']

    def __str__(self):
        return f"{self.name} ({self.line.name})"

    @property
    def hours_since_service(self):
        """Расчёт часов с последнего обслуживания (с учётом таймзон)."""
        if not self.datetime_service:
            return None

        now = timezone.now()
        # Если дата в будущем — считаем, что прошло 0 часов
        if self.datetime_service > now:
            return 0.0

        delta = now - self.datetime_service
        return delta.total_seconds() / 3600  # Возвращает float (например, 4.25 часа)

    @property
    def service_overdue(self):
        """Просрочено ли плановое обслуживание."""
        if not self.service_interval_hours or self.hours_since_service is None:
            return False
        return self.hours_since_service >= self.service_interval_hours

    @property
    def hours_until_next(self):
        """Сколько часов осталось до следующего ТО (для вывода в интерфейс)."""
        if not self.service_interval_hours or self.hours_since_service is None:
            return None
        return max(0, self.service_interval_hours - self.hours_since_service)

class Sensor(models.Model):
    """Датчик на узле линии."""
    sensor_type = models.CharField(
        max_length=100,
        choices=[
            ('temperature', 'Температура'),
            ('pressure', 'Давление'),
            ('vibration', 'Вибрация'),
            ('proximity', 'Приближения'),
            ('photoelectric', 'Фотоэлектрический'),
            ('encoder', 'Энкодер'),
            ('current', 'Ток'),
            ('voltage', 'Напряжение'),
            ('other', 'Другой'),
        ],
        verbose_name='Тип датчика'
    )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='Узел',
        related_name='sensors'
    )
    name = models.CharField(max_length=200, verbose_name='Название датчика')
    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Код/адрес датчика',
        help_text='Адрес в системе управления (например, I0.0, AIW16)'
    )
    photo = models.ImageField(
        upload_to='photos/sensors',
        blank=True,
        null=True,
        verbose_name='Фотография датчика'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    unit_of_measurement = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Единица измерения',
        help_text='°C, бар, мм/с, etc.'
    )
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Мин. значение'
    )
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Макс. значение'
    )
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Текущее значение'
    )
    last_update = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее обновление'
    )

    class Meta:
        ordering = ['node', 'name']
        verbose_name = 'Датчик'
        verbose_name_plural = 'Датчики'
        unique_together = ['node', 'code']

    def __str__(self):
        return f"{self.name} ({self.node.name})"

    @property
    def is_in_range(self):
        """Проверка, находится ли значение в допустимых пределах."""
        if self.current_value is None or self.min_value is None or self.max_value is None:
            return True
        return self.min_value <= self.current_value <= self.max_value
