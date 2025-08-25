from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from expenses import views as expense_views
from rest_framework.authtoken.views import obtain_auth_token

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
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    path("api/signup/", expense_views.api_signup, name="api_signup"),
    path("api/login/", expense_views.api_login, name="api_login"),
    path("api/logout/", expense_views.api_logout, name="api_logout"),
    path("api/me/", expense_views.api_me, name="api_me"),
]