# sps_visualization/models.py

from django.db import models
from sps_lines.models import Line, Node


class LineLayout(models.Model):
    """Схема/чертеж производственной линии."""
    line = models.OneToOneField(
        Line,
        on_delete=models.CASCADE,
        verbose_name='Линия',
        related_name='layout'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название схемы'
    )
    background_image = models.ImageField(
        upload_to='layouts/backgrounds/',
        blank=True,
        null=True,
        verbose_name='Фоновое изображение (чертеж)',
        help_text='Схема линии в формате PNG/SVG'
    )
    width = models.IntegerField(
        default=1920,
        verbose_name='Ширина (px)'
    )
    height = models.IntegerField(
        default=1080,
        verbose_name='Высота (px)'
    )
    scale = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0,
        verbose_name='Масштаб'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')

    class Meta:
        verbose_name = 'Схема линии'
        verbose_name_plural = 'Схемы линий'

    def __str__(self):
        return f"Схема {self.line.name}"


class NodePosition(models.Model):
    """Позиция узла на схеме линии."""
    layout = models.ForeignKey(
        LineLayout,
        on_delete=models.CASCADE,
        verbose_name='Схема',
        related_name='node_positions'
    )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='Узел',
        related_name='positions'
    )
    x = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Позиция X (px)',
        help_text='Координата X на схеме'
    )
    y = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Позиция Y (px)',
        help_text='Координата Y на схеме'
    )
    width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=100,
        verbose_name='Ширина (px)'
    )
    height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=60,
        verbose_name='Высота (px)'
    )
    rotation = models.IntegerField(
        default=0,
        verbose_name='Поворот (градусы)',
        help_text='Угол поворота элемента'
    )
    z_index = models.IntegerField(
        default=1,
        verbose_name='Слой Z',
        help_text='Порядок наложения (больше = выше)'
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Иконка',
        help_text='CSS класс иконки или путь к изображению'
    )
    color = models.CharField(
        max_length=20,
        default='#4CAF50',
        verbose_name='Цвет',
        help_text='Цвет элемента (hex)'
    )

    class Meta:
        verbose_name = 'Позиция узла'
        verbose_name_plural = 'Позиции узлов'
        unique_together = ['layout', 'node']
        ordering = ['z_index', 'x', 'y']

    def __str__(self):
        return f"{self.node.name} на {self.layout.name} ({self.x}, {self.y})"


class ConnectionLine(models.Model):
    """Соединительная линия между узлами (конвейер, трубопровод и т.д.)."""
    layout = models.ForeignKey(
        LineLayout,
        on_delete=models.CASCADE,
        verbose_name='Схема',
        related_name='connections'
    )
    from_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='От узла',
        related_name='outgoing_connections'
    )
    to_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='До узла',
        related_name='incoming_connections'
    )
    connection_type = models.CharField(
        max_length=50,
        choices=[
            ('conveyor', 'Конвейер'),
            ('pipe', 'Трубопровод'),
            ('cable', 'Кабель'),
            ('mechanical', 'Механическая связь'),
            ('other', 'Другое'),
        ],
        default='conveyor',
        verbose_name='Тип соединения'
    )
    # Координаты точек излома (для кривых Безье или ломаных линий)
    # Храним как JSON: [{"x": 100, "y": 200}, {"x": 300, "y": 400}]
    path_points = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Точки пути',
        help_text='Координаты промежуточных точек'
    )
    color = models.CharField(
        max_length=20,
        default='#2196F3',
        verbose_name='Цвет линии'
    )
    line_width = models.IntegerField(
        default=3,
        verbose_name='Толщина линии'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Соединение'
        verbose_name_plural = 'Соединения'
        ordering = ['layout', 'from_node']

    def __str__(self):
        return f"{self.from_node.name} → {self.to_node.name}"


class VisualizationPreset(models.Model):
    """Предустановка отображения (для разных режимов просмотра)."""
    layout = models.ForeignKey(
        LineLayout,
        on_delete=models.CASCADE,
        verbose_name='Схема',
        related_name='presets'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    # Настройки отображения в JSON
    # Пример: {"show_sensors": true, "show_status": true, "theme": "dark"}
    settings = models.JSONField(
        default=dict,
        verbose_name='Настройки отображения'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='По умолчанию'
    )

    class Meta:
        verbose_name = 'Предустановка отображения'
        verbose_name_plural = 'Предустановки отображения'

    def __str__(self):
        return f"{self.name} ({self.layout.name})"
