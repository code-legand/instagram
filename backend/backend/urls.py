"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('signup/', include('app.urls')), 
    path('login/', include('app.urls')),
    path('logout/', include('app.urls')),
    path('fetch_posts/', include('app.urls')),
    path('fetch_my_posts/', include('app.urls')),
    path('store_posts/', include('app.urls')),
    path('recommendations/', include('app.urls')),
    path('search/', include('app.urls')),
    path('fetch_messages/', include('app.urls')),
    path('store_message/', include('app.urls')),
    path('fetch_status/', include('app.urls')),
    path('store_status/', include('app.urls')),
    path('fetch_profile/', include('app.urls')),
    path('update_profile_pic/', include('app.urls')),
    path('update_bio/', include('app.urls')),
    path('get_image/', include('app.urls')),
    path('fetch_followers/', include('app.urls')),
    path('fetch_following/', include('app.urls')),
    path('fetch_follow_requests/', include('app.urls')),
    path('follow_request/', include('app.urls')),
    path('accept_follow_request/', include('app.urls')),
    path('reject_follow_request/', include('app.urls')),
    path('unfollow/', include('app.urls')),
    path('change_to_private/', include('app.urls')),
    path('change_to_public/', include('app.urls')),

]
