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
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from .models import Event, Participant, Expense, Category
from .serializers import EventSerializer, ParticipantSerializer, ExpenseSerializer, CategorySerializer
from .forms import ParticipantForm

class EventViewSet(viewsets.ModelViewSet):
    """CRUD for events; reads public, writes require auth."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Return per-participant balances for the event."""
        event = self.get_object()
        balances = event.get_balance()
        return Response(balances)
    
    @action(detail=True, methods=['get'])
    def settlement(self, request, pk=None):
        """Return minimal settlement instructions for the event."""
        event = self.get_object()
        settlements = event.get_settlement()
        return Response(settlements)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Create a participant inside this event (auth required by viewset)."""
        event = self.get_object()
        form = ParticipantForm(request.data)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.event = event
            participant.save()
            serializer = ParticipantSerializer(participant)
            return Response(serializer.data, status=201)
        return Response(form.errors, status=400)

class ParticipantViewSet(viewsets.ModelViewSet):
    """CRUD for participants; reads public, writes require auth."""
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ExpenseViewSet(viewsets.ModelViewSet):
    """CRUD for expenses; reads public, writes require auth."""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """Resolve FK/M2M fields from IDs and save the expense."""
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
                raise ValidationError({'event': 'Event with this ID does not exist.'})

        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise ValidationError({'category': 'Category with this ID does not exist.'})

        if split_between_ids:
            if isinstance(split_between_ids, str):
                # Try to parse comma-separated string
                split_between_ids = [s for s in split_between_ids.split(',') if s]
            split_between = Participant.objects.filter(id__in=split_between_ids)
            if split_between.count() != len(split_between_ids):
                raise ValidationError({'split_between': 'One or more participants do not exist.'})

        expense = serializer.save(event=event, category=category)
        if split_between is not None:
            expense.split_between.set(split_between)


# CategoryViewSet for registration in urls.py
class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for categories; reads public, writes require auth (for admin use)."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_participant(request, pk):
    """Delete a participant by ID (auth required)."""
    participant = get_object_or_404(Participant, pk=pk)
    participant.delete()
    return Response({"status": "deleted"})

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_event(request, event_id):
    """Delete an event by ID (auth required)."""
    event = get_object_or_404(Event, pk=event_id)
    event.delete()
    return Response({"status": "deleted"})

# API endpoints for user registration and authentication
@csrf_exempt  # DEV ONLY: we'll replace with proper CSRF handling later
@api_view(["POST"])
@permission_classes([AllowAny])
def api_signup(request):
    """
    API endpoint to register a new user via JSON.
    Expects: {"username": "...", "password": "..."}
    """
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response({"detail": "username a password jsou povinné"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"detail": "Uživatel už existuje"}, status=400)
    User.objects.create_user(username=username, password=password)
    return Response({"detail": "OK"}, status=201)

@csrf_exempt  # DEV ONLY: we'll replace with proper CSRF handling later
@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    """
    API endpoint to log a user in (session cookie).
    Expects: {"username": "...", "password": "..."}
    """
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({"detail": "Neplatné přihlášení"}, status=400)
    login(request, user)
    return Response({"detail": "OK"}, status=200)

@api_view(["POST"])
def api_logout(request):
    """
    API endpoint to log out the current user.
    """
    logout(request)
    return Response({"detail": "OK"}, status=200)

@api_view(["GET"])
@permission_classes([AllowAny])
def api_me(request):
    """
    Returns current session user info (or null if anonymous).
    """
    if request.user.is_authenticated:
        return Response({"username": request.user.username}, status=200)
    return Response({"username": None}, status=200)

# Signup view for user registration
def signup_view(request):
    """Render and process the user sign‑up form."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})