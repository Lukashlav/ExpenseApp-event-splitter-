from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from expenses import views as expense_views

router = DefaultRouter()
router.register(r'events', expense_views.EventViewSet, basename='event')
router.register(r'participants', expense_views.ParticipantViewSet, basename='participant')
router.register(r'expenses', expense_views.ExpenseViewSet, basename='expense')
router.register(r'categories', expense_views.CategoryViewSet, basename='category')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/participants/<int:pk>/delete/', expense_views.delete_participant, name="delete_participant"),
    path('api/events/<int:event_id>/delete/', expense_views.delete_event, name='delete_event'),
]