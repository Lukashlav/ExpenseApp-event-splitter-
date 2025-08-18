from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event, Participant, Expense
from .serializers import EventSerializer, ParticipantSerializer, ExpenseSerializer

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
        name = request.data.get('name')
        email = request.data.get('email')
        if not name or not email:
            return Response({'error': 'Both name and email are required.'}, status=400)
        serializer = ParticipantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(event=event)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        event_id = self.request.data.get('event_id')
        if event_id is not None:
            try:
                event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'event_id': 'Event with this ID does not exist.'})
            serializer.save(event=event)
        else:
            serializer.save()