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
    split_between = serializers.PrimaryKeyRelatedField(
        queryset=Participant.objects.all(), many=True, required=False
    )

    class Meta:
        model = Expense
        fields = ['id', 'description', 'amount', 'payer', 'paid_by', 'event', 'split_between']

    def create(self, validated_data):
        split_between_data = validated_data.pop('split_between', [])
        expense = Expense.objects.create(**validated_data)
        expense.split_between.set(split_between_data)
        return expense

    def update(self, instance, validated_data):
        split_between_data = validated_data.pop('split_between', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if split_between_data is not None:
            instance.split_between.set(split_between_data)
        return instance

class EventSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'participants', 'expenses']