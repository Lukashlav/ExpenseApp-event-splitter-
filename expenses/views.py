from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Event, Participant, Expense, Category
from .serializers import EventSerializer, ParticipantSerializer, ExpenseSerializer, CategorySerializer
from .forms import ParticipantForm

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        event = self.get_object()
        balances = event.get_balance()
        return Response(balances)
    
    @action(detail=True, methods=['get'])
    def settlement(self, request, pk=None):
        event = self.get_object()
        settlements = event.get_settlement()
        return Response(settlements)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
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
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
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
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

@csrf_exempt
def delete_participant(request, pk):
    if request.method == "DELETE":
        participant = get_object_or_404(Participant, pk=pk)
        participant.delete()
        return JsonResponse({"status": "deleted"})
    return JsonResponse({"error": "Invalid request"}, status=400)


# Funkce pro mazání celých eventů
@csrf_exempt
def delete_event(request, event_id):
    if request.method == "DELETE":
        event = get_object_or_404(Event, pk=event_id)
        event.delete()
        return JsonResponse({"status": "deleted"})
    return JsonResponse({"error": "Invalid request"}, status=400)