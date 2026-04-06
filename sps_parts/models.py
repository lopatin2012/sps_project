# sps_parts/models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from sps_lines.models import Node


class PartCategory(models.Model):
    """Категория запчасти (подшипник, ремень, датчик и т.д.)."""
    name = models.CharField(max_length=100, verbose_name='Название категории')
    code = models.CharField(max_length=50, unique=True, verbose_name='Код категории')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Категория запчасти'
        verbose_name_plural = 'Категории запчастей'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Part(models.Model):
    """Запчасть/деталь, которая устанавливается в узлы."""
    name = models.CharField(max_length=200, verbose_name='Название запчасти')
    article = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Артикул/номер детали'
    )
    category = models.ForeignKey(
        PartCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория',
        related_name='parts'
    )
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Производитель'
    )
    compatible_nodes = models.ManyToManyField(
        Node,
        blank=True,
        verbose_name='Совместимые узлы',
        related_name='compatible_parts',
        help_text='Узлы, в которые может быть установлена эта деталь'
    )
    expected_lifetime_hours = models.IntegerField(
        default=0,
        verbose_name='Ожидаемый ресурс (часов)',
        help_text='Рекомендуемый срок службы в рабочих часах'
    )
    photo = models.ImageField(
        upload_to='parts/photos/',
        blank=True,
        null=True,
        verbose_name='Фото запчасти'
    )
    documentation = models.FileField(
        upload_to='parts/docs/',
        blank=True,
        null=True,
        verbose_name='Документация (PDF)'
    )

    class Meta:
        verbose_name = 'Запчасть'
        verbose_name_plural = 'Запчасти'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (арт. {self.article})"


class PartInstallation(models.Model):
    """Установка запчасти в узел - отслеживание жизненного цикла детали."""
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        verbose_name='Запчасть',
        related_name='installations'
    )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='Узел',
        related_name='part_installations'
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Серийный номер'
    )
    installed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата установки'
    )
    removed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата демонтажа'
    )
    installation_hours = models.IntegerField(
        default=0,
        verbose_name='Наработка на момент установки (часов)',
        help_text='Показания счетчика на момент установки'
    )
    current_hours = models.IntegerField(
        default=0,
        verbose_name='Текущая наработка (часов)'
    )
    installed_by = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Установил'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания'
    )

    class Meta:
        verbose_name = 'Установка запчасти'
        verbose_name_plural = 'Установки запчастей'
        ordering = ['-installed_at']
        indexes = [
            models.Index(fields=['node', '-installed_at']),
        ]

    def __str__(self):
        return f"{self.part.name} в {self.node.name} (с {self.installed_at.strftime('%d.%m.%Y')})"

    @property
    def is_installed(self):
        """Запчасть сейчас установлена."""
        return self.removed_at is None

    @property
    def hours_in_operation(self):
        """Часы работы запчасти."""
        if self.is_installed:
            # Здесь должна быть логика получения текущей наработки узла
            return self.current_hours - self.installation_hours
        else:
            return self.current_hours - self.installation_hours

    @property
    def remaining_lifetime_hours(self):
        """Оставшийся ресурс (часов)."""
        if self.part.expected_lifetime_hours == 0:
            return None
        remaining = self.part.expected_lifetime_hours - self.hours_in_operation
        return max(0, remaining)

    @property
    def lifetime_percentage(self):
        """Процент износа."""
        if self.part.expected_lifetime_hours == 0:
            return 0
        percentage = (self.hours_in_operation / self.part.expected_lifetime_hours) * 100
        return min(100, percentage)

    @property
    def needs_replacement_soon(self):
        """Требуется ли скорая замена (осталось < 10% ресурса)."""
        if self.remaining_lifetime_hours is None:
            return False
        return self.remaining_lifetime_hours < (self.part.expected_lifetime_hours * 0.1)

    @property
    def is_overdue(self):
        """Ресурс исчерпан."""
        if self.remaining_lifetime_hours is None:
            return False
        return self.remaining_lifetime_hours <= 0


class Warehouse(models.Model):
    """Склад запчастей."""
    name = models.CharField(max_length=200, verbose_name='Название склада')
    code = models.CharField(max_length=50, unique=True, verbose_name='Код склада')
    location = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Расположение'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class SparePartStock(models.Model):
    """Запчасть на складе."""
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        verbose_name='Запчасть',
        related_name='stock_items'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name='Склад',
        related_name='stock_items'
    )
    quantity = models.IntegerField(
        default=0,
        verbose_name='Количество',
        validators=[MinValueValidator(0)]
    )
    min_stock_level = models.IntegerField(
        default=1,
        verbose_name='Минимальный запас',
        help_text='При достижении этого количества нужно заказать'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Место на складе',
        help_text='Ячейка/полка/стеллаж'
    )
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Запчасть на складе'
        verbose_name_plural = 'Запчасти на складе'
        unique_together = ['part', 'warehouse']
        ordering = ['warehouse', 'part']

    def __str__(self):
        return f"{self.part.name}: {self.quantity} шт. ({self.warehouse})"

    @property
    def is_low_stock(self):
        """Низкий остаток."""
        return self.quantity <= self.min_stock_level

    @property
    def is_out_of_stock(self):
        """Нет в наличии."""
        return self.quantity == 0


class PartOrder(models.Model):
    """Заказ запчасти (в пути)."""
    STATUS_CHOICES = [
        ('ordered', 'Заказан'),
        ('confirmed', 'Подтвержден'),
        ('shipped', 'Отгружен'),
        ('in_transit', 'В пути'),
        ('customs', 'На таможне'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        verbose_name='Запчасть',
        related_name='orders'
    )
    quantity = models.IntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )
    supplier = models.CharField(
        max_length=200,
        verbose_name='Поставщик'
    )
    order_number = models.CharField(
        max_length=100,
        verbose_name='Номер заказа'
    )
    order_date = models.DateField(
        auto_now_add=True,
        verbose_name='Дата заказа'
    )
    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Ожидаемая дата доставки'
    )
    actual_delivery_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Фактическая дата доставки'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ordered',
        verbose_name='Статус'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Цена за единицу'
    )
    currency = models.CharField(
        max_length=3,
        default='RUB',
        verbose_name='Валюта'
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Трекинг-номер'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Заказ запчасти'
        verbose_name_plural = 'Заказы запчастей'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['status', 'expected_delivery_date']),
        ]

    def __str__(self):
        return f"Заказ {self.order_number}: {self.part.name} ({self.quantity} шт.)"

    @property
    def total_price(self):
        """Общая стоимость."""
        if self.price:
            return self.price * self.quantity
        return None

    @property
    def days_until_delivery(self):
        """Дней до доставки."""
        if self.expected_delivery_date and self.status not in ['delivered', 'cancelled']:
            delta = self.expected_delivery_date - timezone.now().date()
            return delta.days
        return None

    @property
    def is_overdue(self):
        """Просрочен ли заказ."""
        if self.expected_delivery_date and self.status not in ['delivered', 'cancelled']:
            return timezone.now().date() > self.expected_delivery_date
        return False
