# sps_dashboard/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.db.models import F
from django.core.paginator import Paginator
from django.contrib import messages

from sps_lines.models import Line, Node, Sensor
from sps_events.models import Event
from sps_parts.models import PartInstallation, SparePartStock

from sps_dashboard.forms import EventCreateForm

from sps_events.utils import log_status_change

# TODO -----------------------  Линии -----------------------
class LineListView(ListView):
    """Главная страница. Список всех производственных линий."""
    model = Line
    template_name = 'sps_dashboard/line_list.html'
    context_object_name = 'lines'

    def get_queryset(self):
        """Только активные линии."""
        return Line.objects.filter(
            is_active=True,
            datetime_decommissioning__isnull=True
        ).prefetch_related('nodes', 'nodes__sensors')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lines = context['lines']

        # Общая статистика
        context['total_lines'] = lines.count()

        # Подсчёт по статусам
        status_counts = {
            'running': 0,
            'warning': 0,
            'error': 0,
            'inactive': 0,
            'maintenance': 0,
        }

        for line in lines:
            status = line.get_status()
            if status in status_counts:
                status_counts[status] += 1

        context['status_counts'] = status_counts

        context['active_lines'] = status_counts['running']
        context['problem_lines'] = status_counts['warning'] + status_counts['error']
        context['inactive_lines'] = status_counts['inactive'] + status_counts['maintenance']

        return context


class LineDetailView(DetailView):
    """Детальная информация производственной линии."""
    model = Line
    template_name = 'sps_dashboard/line_detail.html'
    context_object_name = 'line'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        line = self.object

        # Узлы линии.
        context['nodes'] = line.nodes.all().prefetch_related('sensors')

        # Статистика по узлам.
        context['nodes'] = line.nodes.all().prefetch_related('sensors')
        context['total_nodes'] = line.nodes.count()
        context['active_nodes'] = line.nodes.filter(is_active=True).count()
        context['problem_nodes'] = line.nodes.filter(is_active=False).count()

        # Датчики.
        total_sensors = 0
        ok_sensor = 0
        for node in line.nodes.all():
            for sensor in node.sensors.all():
                total_sensors += 1
                if sensor.is_in_range:
                    ok_sensor += 1

        context['total_sensors'] = total_sensors
        context['ok_sensors'] = ok_sensor
        context['warning_sensors'] = total_sensors - ok_sensor

        # Запчасти с критическим ресурсом.
        context['critical_parts'] = PartInstallation.objects.filter(
            node__line=line,
            removed_at__isnull=True
        ).select_related('part', 'node').order_by('part__expected_lifetime_hours')[:5]

        # Запчасти с низким остатком на складе.
        context['low_stock_parts'] = SparePartStock.objects.filter(
            part__compatible_nodes__line=line
        ).filter(
            quantity__lte=F('min_stock_level')
        ).select_related('part', 'warehouse').distinct()[:5]

        # Последние 5 событий.
        context['recent_events'] = line.events.all()[:5]

        return context

# TODO ----------------------- Линии (AJAX) -----------------------

class LineStatusView(View):
    """AJAX-эндпоинт. Получение статуса линии."""

    def get(self, request, pk):
        cache_key = f'line_status_{pk}'

        # Пытаемся получить из кэша только статус и время
        cached_status = cache.get(cache_key)

        if cached_status and request.headers.get('HX-Request'):
            # Используем кэшированные данные
            data = {
                'status': cached_status['status'],
                'updated_at': cached_status['updated_at'],
                'pk': pk,
                'request': request  #
            }
            return render(request, 'sps_dashboard/_partials/line_status_badge.html', data)

        # Получаем данные из БД
        line = get_object_or_404(
            Line.objects.prefetch_related('nodes', 'nodes__sensors'),
            pk=pk
        )

        # Определение статуса
        status = line.get_status()

        # Данные для кэша
        cache_data = {
            'status': status,
            'updated_at': timezone.now().strftime('%H:%M:%S'),
        }

        # Сохраняем в кэш на 2 секунды
        cache.set(cache_key, cache_data, 2)

        # Данные для ответа
        data = {
            **cache_data,
            'pk': pk,
            'request': request
        }

        if request.headers.get('HX-Request'):
            return render(request, 'sps_dashboard/_partials/line_status_badge.html', data)
        else:
            return JsonResponse(data)

class LineNodesView(View):
    """AJAX-эндпоинт. Таблица узлов. Для HTMX с фильтрами."""
    def get(self, request, pk):
        line = get_object_or_404(Line, pk=pk)
        search = request.GET.get('search', '')

        nodes = line.nodes.all().prefetch_related('sensors')

        if search:
            nodes = nodes.filter(name__icontains=search)

        return render(
            request,
            'sps_dashboard/_partials/nodes_table.html',
            {
                'nodes': nodes,
                'line': line,
                'request': request
            }
        )

class LineEventsView(View):
    """AJAX-эндпоинт. Вкладка событий линии."""

    def get(self, request, pk):
        line = get_object_or_404(Line, pk=pk)

        # Фильтры
        event_type = request.GET.get('event_type', '')
        severity = request.GET.get('severity', '')
        page = request.GET.get('page', '')

        events = line.events.all().select_related('node', 'sensor', 'user')

        if event_type:
            events = events.filter(event_type=event_type)
        if severity:
            events = events.filter(severity=severity)

        # Пагинация
        paginator = Paginator(events, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        is_partial = request.GET.get('partial') == '1'

        context = {
            'line': line,
            'page_obj': page_obj,
            'event_type': event_type,
            'severity': severity,
            'request': request,
        }

        if is_partial:
            return render(request, 'sps_dashboard/_partials/events_list.html', context)
        else:
            return render(request, 'sps_dashboard/_partials/events_tab.html', context)

# TODO ----------------------- События -----------------------

class EventCreateView(View):
    """Создание события через форму."""
    def post(self, request, line_pk):
        line = get_object_or_404(Line, pk=line_pk)

        form = EventCreateForm(request.POST, line=line)

        if form.is_valid():
            event = form.save(commit=False)
            event.line = line
            event.user = request.user or None

            # При выборе узла, привязываем датчик.
            if form.cleaned_data.get('node'):
                event.node = form.cleaned_data['node']
            if form.cleaned_data.get('sensor'):
                event.sensor = form.cleaned_data['sensor']

            event.save()

            messages.success(request, f'Событие "{event.title}" создано')

            # Возврат.
            return redirect('sps_dashboard:line_detail', pk=line_pk)
        else:
            # Ошибка.
            messages.error(request, 'Проверьте правильность заполнения формы')
            return redirect('sps_dashboard:line_detail', pk=line_pk)

class EventUpdateView(View):
    """Редактирование события."""
    def get(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        form = EventCreateForm(instance=event, line=event.line)
        return render(
            request,
            'sps_dashboard/_partials/event_edit_form.html',
            {
                'form': form,
                'event': event,
            }
        )

    def post(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        form = EventCreateForm(request.POST, instance=event, line=event.line)

        if form.is_valid():
            form.save()
            messages.success(request, 'Событие обновлено')
            return self._refresh_events_list(event.line)

        return render(
            request,
            'sps_dashboard/_partials/event_edit_form.html',
            {
                'form': form,
                'event': event,
            }
        )

    def _refresh_events_list(self, line):
        """Возврат обновлённого списка событий."""
        events = line.events.all().select_related('node', 'sensor', 'user')
        paginator = Paginator(events, 20)
        page_obj = paginator.get_page(1)
        return render(
            self.request,
            'sps_dashboard/_partials/events_list.html',
            {
                'line': line,
                'page_obj': page_obj,
                'event_type': '',
                'severity': ''
            }
        )


class EventDeleteView(View):
    """Удалить событие."""
    def get(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        return render(
            request,
            'sps_dashboard/_partials/event_delete_confirm.html',
            {
                'event': event,
            }
        )

    def post(self, request, event_pk):
        event = get_object_or_404(Event, pk=event_pk)
        line = event.line
        event.delete()
        messages.success(request, 'Событие удалено')
        return self._refresh_events_list(line)

    def _refresh_events_list(self, line):
        """Вспомогательный метод для возврата обновлённого списка событий."""
        events = line.events.all().select_related('node', 'sensor', 'user')
        paginator = Paginator(events, 20)
        page_obj = paginator.get_page(1)
        return render(
            self.request,
            'sps_dashboard/_partials/events_list.html',
            {
                'line': line,
                'page_obj': page_obj,
                'event_type': '',
                'severity': ''
            }
        )
