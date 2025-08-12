from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
import expenses.views

router = DefaultRouter()
router.register(r'events', expenses.views.EventViewSet, basename='event')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]