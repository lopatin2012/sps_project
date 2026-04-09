# sps_dashboard/forms.py

from django.utils import timezone
from django import forms
from sps_events.models import Event
from sps_lines.models import Line, Node, Sensor

from helpers.enums import EnumEventType, EnumSeverity


class DateTimeLocalInput(forms.DateTimeInput):
    """Виджет для <input type="datetime-local"> с корректным форматом и стилями."""
    input_type = 'datetime-local'

    def __init__(self, attrs=None, format=None):

        default_attrs = {'class': 'form-input'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format=format)

    def format_value(self, value):

        """Форматирует datetime в YYYY-MM-DDTHH:MM и убирает таймзону."""
        if value is None:
            return ''

        if timezone.is_aware(value):
            value = timezone.localtime(value)

        return value.strftime('%Y-%m-%dT%H:%M')


class NodeForm(forms.ModelForm):
    """Форма создания/редактирования узла."""

    inventory_number = forms.CharField(
        required=False,
        label='Инвентарный номер узла',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Инв. номер (опционально)'
        })
    )

    datetime_service = forms.DateTimeField(
        required=False,
        label='Дата последнего обслуживания',
        widget=DateTimeLocalInput(),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    service_interval_hours = forms.IntegerField(
        required=False,
        min_value=0,
        label='Интервал обслуживания (часов)',
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0',
            'step': '1'
        })
    )

    position_x = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        label='Позиция X (%)',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )
    position_y = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        label='Позиция Y (%)',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )
    position_z = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        label='Позиция Z (глубина)',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'})
    )

    class Meta:
        model = Node
        fields = ['node_type', 'name', 'inventory_number', 'is_active',
                  'datetime_service', 'service_interval_hours',
                  'position_x', 'position_y', 'position_z']
        widgets = {
            'node_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название узла *',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class EventForm(forms.ModelForm):
    """Создание и редактирования события."""

    severity = forms.ChoiceField(
        choices=[
            (EnumSeverity.info.name, EnumSeverity.info.value),
            (EnumSeverity.success.name, EnumSeverity.success.value),
            (EnumSeverity.warning.name, EnumSeverity.warning.value),
            (EnumSeverity.error.name, EnumSeverity.error.value),
            (EnumSeverity.critical.name, EnumSeverity.critical.value)
        ],
        initial=EnumSeverity.info.name,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    event_type = forms.ChoiceField(
        choices=[
            (EnumEventType.status_change.name, EnumEventType.status_change.value),
            (EnumEventType.node_error.name, EnumEventType.node_error.value),
            (EnumEventType.sensor_alert.name, EnumEventType.sensor_alert.value),
            (EnumEventType.maintenance.name, EnumEventType.maintenance.value),
            (EnumEventType.part_replace.name, EnumEventType.part_replace.value),
            (EnumEventType.manual.name, EnumEventType.manual.value),
            (EnumEventType.system.name, EnumEventType.system.value),
        ]
    )

    node = forms.ModelChoiceField(
        queryset=Node.objects.none(),
        required=False,
        empty_label='-- Все узлы --',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    sensor = forms.ModelChoiceField(
        queryset=Sensor.objects.none(),
        required=False,
        empty_label='-- Все датчики --',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Event
        fields = ('event_type', 'severity', 'title', 'message', 'node', 'sensor')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Краткий заголовок события',
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 6px;'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Подробное описание (желательно)',
                'rows': 3,
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 6px; resize: vertical;'
            }),
            'event_type': forms.Select(attrs={
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 6px;'
            }),
            'severity': forms.Select(attrs={
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 6px;'
            }),
            'node': forms.Select(attrs={
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 6px;'
            }),
            'sensor': forms.Select(attrs={
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #e5e7eb; border-radius: 6px;'
            }),
        }

    def __init__(self, *args, line=None, **kwargs):
        super().__init__(*args, **kwargs)
        if line:
            # Фильтрация узлов и датчиков по линии.
            self.fields['node'].queryset = Node.objects.filter(line=line)
            self.fields['sensor'].queryset = Sensor.objects.filter(node__line=line)
