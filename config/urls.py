"""
URL configuration for ExpenseApp.
Defines API endpoints and routes for admin, DRF viewsets, and authentication helpers.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from expenses import views as expense_views

# Register API endpoints with DRF router
router = DefaultRouter(trailing_slash='/?')
router.register(r'events', expense_views.EventViewSet, basename='event')
router.register(r'participants', expense_views.ParticipantViewSet, basename='participant')
router.register(r'expenses', expense_views.ExpenseViewSet, basename='expense')
router.register(r'categories', expense_views.CategoryViewSet, basename='category')

# Explicit URL patterns for admin and custom API actions
urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin site
    path('api/', include(router.urls)),  # DRF router-generated endpoints
    path('api/participants/<int:pk>/delete/', expense_views.delete_participant, name="delete_participant"),  # Delete participant
    path('api/events/<int:event_id>/delete/', expense_views.delete_event, name='delete_event'),  # Delete event
    path("api/signup/", expense_views.api_signup, name="api_signup"),  # User signup
    path("api/login/", expense_views.api_login, name="api_login"),  # User login
    path("api/logout/", expense_views.api_logout, name="api_logout"),  # User logout
    path("api/me/", expense_views.api_me, name="api_me"),  # Current session info
    path("api/csrf/", expense_views.api_csrf, name="api_csrf"),  # CSRF bootstrap endpoint
]

# Consistent JSON error handlers (implemented in expenses.views)
handler400 = 'expenses.views.api_bad_request'
handler403 = 'expenses.views.api_permission_denied'
handler404 = 'expenses.views.api_not_found'
handler500 = 'expenses.views.api_server_error'