from django.urls import path

from . import views

app_name = 'vdpurls'

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home-base'),
    path('vdp/<str:highlight>/', views.vdp_urls, name='vdp-urls'),
]
