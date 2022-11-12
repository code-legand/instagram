from django.contrib import admin
from django.urls import path, include
from app import views


urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('getposts/', views.get_posts, name='getposts'),
    path('recommendations/', views.recommendations, name='recommendations'),
]