from django.urls import re_path
from django.contrib import admin
from django.conf.urls.static import serve
from django.urls import path, include
from django.conf.urls import handler404, handler500, handler403
from errorPages import views
from . import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^', include('authApp.urls')),
    re_path(r'^', include('survey.urls')),
    re_path(r'^', include('reports.urls')),
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),

]
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT
        })
    ] 

handler403 = views.error403
handler404 = views.error_404

