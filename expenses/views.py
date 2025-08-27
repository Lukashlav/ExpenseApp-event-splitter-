"""
Views for ExpenseApp.
Provide REST API endpoints (via DRF ViewSets and function-based views) for events, participants, expenses, categories, and user authentication.
"""
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from .models import Event, Participant, Expense, Category
from .serializers import EventSerializer, ParticipantSerializer, ExpenseSerializer, CategorySerializer
from .forms import ParticipantForm

class EventViewSet(viewsets.ModelViewSet):
    """CRUD API for events. Public can list/retrieve; authenticated users can create/update/delete."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Return per-participant balances for this event."""
        event = self.get_object()
        balances = event.get_balance()
        return Response(balances)
    
    @action(detail=True, methods=['get'])
    def settlement(self, request, pk=None):
        """Return settlement instructions (who pays whom) to balance this event."""
        event = self.get_object()
        settlements = event.get_settlement()
        return Response(settlements)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Create a new participant inside this event. Requires auth + CSRF."""
        event = self.get_object()
        form = ParticipantForm(request.data)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.event = event
            try:
                participant.save()
            except DjangoValidationError as e:
                detail = getattr(e, 'message_dict', None) or {'non_field_errors': e.messages}
                return Response(detail, status=400)
            serializer = ParticipantSerializer(participant)
            return Response(serializer.data, status=201)
        return Response(form.errors, status=400)


class ParticipantViewSet(viewsets.ModelViewSet):
    """CRUD API for participants. Public can list/retrieve; authenticated can write."""
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# Delete participant endpoint (auth required)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_participant(request, pk):
    """Delete a participant by primary key. Requires authenticated session."""
    participant = get_object_or_404(Participant, pk=pk)
    participant.delete()
    return Response(status=204)

# Delete event endpoint (auth required)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_event(request, event_id):
    """Delete an event by primary key. Requires authenticated session."""
    event = get_object_or_404(Event, pk=event_id)
    event.delete()
    return Response(status=204)

class ExpenseViewSet(viewsets.ModelViewSet):
    """CRUD API for expenses. Public can list/retrieve; authenticated can write."""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """Resolve foreign keys and M2M fields from IDs, validate existence, and save the expense."""
        # Get event, category, split_between from request data
        event_id = self.request.data.get('event')
        category_id = self.request.data.get('category')
        split_between_ids = self.request.data.get('split_between_ids')

        event = None
        category = None
        split_between = None

        if event_id:
            try:
                event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist:
                raise ValidationError({'event': 'Událost s tímto ID neexistuje.'})

        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise ValidationError({'category': 'Kategorie s tímto ID neexistuje.'})

        if split_between_ids:
            if isinstance(split_between_ids, str):
                # Try to parse comma-separated string
                split_between_ids = [s for s in split_between_ids.split(',') if s]
            split_between = Participant.objects.filter(id__in=split_between_ids)
            if split_between.count() != len(split_between_ids):
                raise ValidationError({'split_between_ids': 'Jeden nebo více účastníků neexistuje.'})

        try:
            expense = serializer.save(event=event, category=category)
            if split_between is not None:
                expense.split_between.set(split_between)
            return expense
        except DjangoValidationError as e:
            detail = getattr(e, 'message_dict', None) or {'non_field_errors': e.messages}
            if isinstance(detail, dict) and 'split_between' in detail and 'split_between_ids' not in detail:
                detail['split_between_ids'] = detail.pop('split_between')
            raise ValidationError(detail)


# CategoryViewSet for registration in urls.py
class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD API for categories (mainly for admin use). Public can read; authenticated can write."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def api_csrf(request):
    """Issue a CSRF cookie for the client. Call once from frontend before POSTs."""
    return Response({"detail": "CSRF cookie set"}, status=200)

# API endpoints for user registration and authentication
@api_view(["POST"])
@permission_classes([AllowAny])
def api_signup(request):
    """Register a new user via JSON body {"username":..., "password":...}."""
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response({"detail": "username a password jsou povinné"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"detail": "Uživatel už existuje"}, status=400)
    User.objects.create_user(username=username, password=password)
    return Response({"detail": "OK"}, status=201)

@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    """Authenticate user and create session cookie. Expects JSON {"username":..., "password":...}."""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"detail": "Neplatné přihlášení"}, status=401)
    login(request, user)
    return Response({"detail": "OK"}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """Log out the current user. Requires authenticated session + CSRF."""
    logout(request)
    return Response({"detail": "OK"}, status=200)

@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def api_me(request):
    """Return current session user info and auth flag. Also ensures CSRF cookie is set."""
    if request.user.is_authenticated:
        return Response({
            "authenticated": True,
            "username": request.user.username,
        }, status=200)
    return Response({
        "authenticated": False,
        "username": None,
    }, status=200)

# Signup view for user registration
def signup_view(request):
    """Render and process a classic Django sign-up form (HTML)."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def api_bad_request(request, exception):
    return JsonResponse(
        {"detail": "Špatný požadavek", "status": 400, "path": request.path},
        status=400
    )

def api_permission_denied(request, exception):
    return JsonResponse(
        {"detail": "Přístup odepřen", "status": 403, "path": request.path},
        status=403
    )

def api_not_found(request, exception):
    return JsonResponse(
        {"detail": "Nenalezeno", "status": 404, "path": request.path},
        status=404
    )

def api_server_error(request):
    return JsonResponse(
        {"detail": "Interní chyba serveru", "status": 500, "path": request.path},
        status=500
    )
