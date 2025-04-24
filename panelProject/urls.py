"""panelProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
    # 后台
    path('api/admin/', admin.site.urls),

    # 正式版 url
    path('api/aws/', include('apps.aws.urls')),
    path('api/azure/', include('apps.azure.urls')),
    path('api/passport/', include('apps.users.urls')),
    path('api/linode/', include('apps.linode.urls')),
    path('api/do/', include('apps.do.urls')),
    path('api/users/', include('apps.users.urls'))
]
