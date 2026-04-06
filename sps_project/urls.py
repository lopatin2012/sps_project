from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


from sps_project.settings import DEBUG
from sps_project.settings import MEDIA_URL
from sps_project.settings import MEDIA_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sps_dashboard.urls')),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)

if DEBUG:
    urlpatterns += staticfiles_urlpatterns()
