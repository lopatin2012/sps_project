from django.urls import path
from . import views

app_name = 'sps_dashboard' # Дашборды.

urlpatterns = [
    # Главная страница. Список всех линий.
    path('', views.LineListView.as_view(), name='line_list'),

    # Детализация линии.
    path('line/<int:pk>/', views.LineDetailView.as_view(), name='line_detail'),

    # События.

        # Создание.
    path('line/<int:line_pk>/event/create/', views.EventCreateView.as_view(), name='event_create'),

    # AJAX-эндпоинты для HTMX
    path('line/<int:pk>/status/', views.LineStatusView.as_view(), name='line_status'),
    path('line/<int:pk>/nodes/', views.LineNodesView.as_view(), name='line_nodes'),
    path('line/<int:pk>/events/', views.LineEventsView.as_view(), name='line_events'),

]