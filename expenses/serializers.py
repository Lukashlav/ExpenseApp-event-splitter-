from rest_framework import serializers
from .models import Event, Participant, Expense, Category

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'name', 'email']

class ExpenseSerializer(serializers.ModelSerializer):
    payer = serializers.PrimaryKeyRelatedField(
        queryset=Participant.objects.all()
    )
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    split_between = ParticipantSerializer(many=True, read_only=True)
    split_between_ids = serializers.PrimaryKeyRelatedField(
        queryset=Participant.objects.all(), many=True, write_only=True, source='split_between'
    )

    class Meta:
        model = Expense
        fields = [
            'id',
            'description',
            'amount',
            'payer',
            'event',
            'category',
            'split_between',
            'split_between_ids'
        ]

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

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['payer'] = {
            'id': instance.payer.id,
            'name': instance.payer.name,
            'email': instance.payer.email
        } if instance.payer else None

        rep['category'] = {
            'id': instance.category.id,
            'name': instance.category.name
        } if instance.category else None

        rep['split_between'] = [
            {'id': p.id, 'name': p.name, 'email': p.email} for p in instance.split_between.all()
        ]

        return rep

class EventSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'participants', 'expenses']
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']