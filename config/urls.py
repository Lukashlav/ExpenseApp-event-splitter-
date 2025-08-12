from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
import expenses.views

router = DefaultRouter()
router.register(r'events', expenses.views.EventViewSet, basename='event')
router.register(r'participants', expenses.views.ParticipantViewSet, basename='participant')
router.register(r'expenses', expenses.views.ExpenseViewSet, basename='expense')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]