from django.urls import path

from . import views

app_name='creators'
urlpatterns = [
    path('', views.index, name='index'),
    path('channels/', views.channels, name='channels'),
    path('channels/<str:channel_id>/', views.detail, name='detail')

]
