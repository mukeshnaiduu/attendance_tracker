"""
URL configuration for attendance_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test

def anonymous_required(function=None, redirect_url=None):
    actual_decorator = user_passes_test(
        lambda u: not u.is_authenticated,
        login_url=redirect_url or 'dashboard'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('attendance.urls')),
]
