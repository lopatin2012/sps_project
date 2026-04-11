from django.urls import path
from . import views

app_name = 'sps_dashboard' # Дашборды.

urlpatterns = [
    # Главная страница. Список всех линий.
    path('', views.LineListView.as_view(), name='line_list'),

    # Детализация линии.
    path('line/<int:pk>/', views.LineDetailView.as_view(), name='line_detail'),

    # Узлы.
        # Создание.
    path('line/<int:line_pk>/node/create/', views.NodeCreateView.as_view(), name='node_create'),
        # Редактирование.
    path('node/<int:node_pk>/edit/', views.NodeUpdateView.as_view(), name='node_edit'),
        # Удаление.
    path('node/<int:node_pk>/delete/', views.NodeDeleteView.as_view(), name='node_delete'),
    # Управление ТО узлов
    path(
        'node/<int:node_pk>/maintenance/start/',
        views.NodeStartMaintenanceView.as_view(),
        name='node_maintenance_start'
    ),
    path(
        'node/<int:node_pk>/maintenance/finish/',
        views.NodeFinishMaintenanceView.as_view(),
        name='node_maintenance_finish'
    ),

    # Датчики.
        # Создание.
    path('node/<int:node_pk>/sensor/create/', views.SensorCreateView.as_view(), name='sensor_create'),
        # Редактирование.
    path('sensor/<int:sensor_pk>/edit/', views.SensorUpdateView.as_view(), name='sensor_edit'),
        # Удаление.
    path('sensor/<int:sensor_pk>/delete/', views.SensorDeleteView.as_view(), name='sensor_delete'),


    # События.
        # Создание.
    path('line/<int:line_pk>/event/create/', views.EventCreateView.as_view(), name='event_create'),
        # Редактирование.
    path('event/<int:event_pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
        # Удаление.
    path('event/<int:event_pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),

    # AJAX-эндпоинты для HTMX
    path('line/<int:pk>/status/', views.LineStatusView.as_view(), name='line_status'),
    path('line/<int:pk>/nodes/', views.LineNodesView.as_view(), name='line_nodes'),
    path('line/<int:pk>/events/', views.LineEventsView.as_view(), name='line_events'),

]