from django.urls import path
from .views import *
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('', index, name='home'),
    path('home/home-index/', home_index, name='home-index'),
    path('home/search_index/', Search.as_view(), name='search'),
    path('home/report_index/', Report.as_view(), name='report'),
    path('get_diagnoses/', views.get_diagnoses, name='get_diagnoses'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)