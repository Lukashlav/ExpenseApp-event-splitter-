from rest_framework import serializers
from .models import Event, Participant, Expense

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'name', 'email']

class ExpenseSerializer(serializers.ModelSerializer):
    payer = ParticipantSerializer(read_only=True)
    paid_by = serializers.PrimaryKeyRelatedField(
        queryset=Participant.objects.all(), write_only=True, source='payer'
    )
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = Expense
        fields = ['id', 'description', 'amount', 'payer', 'paid_by', 'event']

class EventSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'participants', 'expenses']