from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('compare/', views.compare, name='compare'),
    path('download_compared/', views.download_compared, name='download_compared'),
    path('download_amazon/', views.download_amazon, name='download_amazon'),
    path('download_flipcart/', views.download_flipcart, name='download_flipcart'),
    ]
