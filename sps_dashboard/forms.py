# sps_dashboard/forms.py

from django import forms
from sps_events.models import Event
from sps_lines.models import Line, Node, Sensor

from helpers.enums import EnumEventType, EnumSeverity


class EventCreateForm(forms.ModelForm):
    """Создание события."""

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