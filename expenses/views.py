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

class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    