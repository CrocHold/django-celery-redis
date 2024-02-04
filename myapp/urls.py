from django.urls import path
from myapp import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('api/videos/', views.query, name = 'query')
]