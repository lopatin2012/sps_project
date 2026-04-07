from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views


from sps_project.settings import DEBUG
from sps_project.settings import MEDIA_URL
from sps_project.settings import MEDIA_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sps_dashboard.urls')),

    # Встроенная авторизация.
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),

    # Выход из системы.
    path('logout/', auth_views.LogoutView.as_view(
        next_page='sps_dashboard:line_list',
    ), name='logout'),

] + static(MEDIA_URL, document_root=MEDIA_ROOT)

if DEBUG:
    urlpatterns += staticfiles_urlpatterns()
