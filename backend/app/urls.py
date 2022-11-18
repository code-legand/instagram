from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('fetch_posts/', views.fetch_posts, name='fetchposts'),
    path('fetch_my_posts/', views.fetch_my_posts, name='fetchmyposts'),
    path('store_post/', views.store_post, name='storepost'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('search/', views.search, name='search'),
    path('fetch_messages/', views.fetch_messages, name='fetchmessages'),
    path('store_message/', views.store_message, name='storemessage'),
    path('fetch_status/', views.fetch_status, name='fetchstatus'),
    path('store_status/', views.store_status, name='storestatus'),
    path('fetch_profile/', views.fetch_profile, name='fetchprofile'),
    path('update_profile_pic/', views.update_profile_pic, name='updateprofilepic'),
    path('update_bio/', views.update_bio, name='updatebio'),
    path('get_image/', views.get_image, name='getimage'),
]