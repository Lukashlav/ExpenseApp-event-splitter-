"""
Serializers for ExpenseApp.
Provide JSON representations and validation for participants, expenses, events and categories.
"""
from rest_framework import serializers
from .models import Event, Participant, Expense, Category

class ParticipantSerializer(serializers.ModelSerializer):
    """Serialize a participant (id, name, email)."""
    class Meta:
        model = Participant
        fields = ['id', 'name', 'email']

class ExpenseSerializer(serializers.ModelSerializer):
    """Serialize an expense including payer, event, optional category and split participants."""
    payer = serializers.PrimaryKeyRelatedField(
        queryset=Participant.objects.all()
    )
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    split_between = ParticipantSerializer(many=True, read_only=True)
    # Write-only helper to accept participant IDs for split_between.
    split_between_ids = serializers.PrimaryKeyRelatedField(
        queryset=Participant.objects.all(), many=True, write_only=True, source='split_between', required=False
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

    def validate(self, attrs):
        """Validate cross-model constraints (payer/split participants belong to the same event, amount > 0)."""
        # Ensure payer and split_between participants belong to the same event
        event = attrs.get('event') or getattr(self.instance, 'event', None)
        payer = attrs.get('payer') or getattr(self.instance, 'payer', None)
        split_between = attrs.get('split_between', None)  # may be None on partial update

        if event is None:
            # event should always be provided on create; on update it's on instance
            raise serializers.ValidationError({ 'event': 'Event is required.' })

        if payer and not event.participants.filter(pk=payer.pk).exists():
            raise serializers.ValidationError({ 'payer': 'Payer must be a participant of this event.' })

        if split_between is not None:
            invalid = [p.id for p in split_between if not event.participants.filter(pk=p.pk).exists()]
            if invalid:
                raise serializers.ValidationError({ 'split_between_ids': 'All selected participants must belong to this event.' })

        amount = attrs.get('amount', None)
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({ 'amount': 'Amount must be a positive number.' })

        return attrs

    def create(self, validated_data):
        """Create an expense and set its many-to-many split participants."""
        split_between_data = validated_data.pop('split_between', [])
        expense = Expense.objects.create(**validated_data)
        expense.split_between.set(split_between_data)
        return expense

    def update(self, instance, validated_data):
        """Update primitive fields and (optionally) replace split participants."""
        split_between_data = validated_data.pop('split_between', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if split_between_data is not None:
            instance.split_between.set(split_between_data)
        return instance

    def to_representation(self, instance):
        """Return a rich JSON payload with nested payer/category/split participants."""
        rep = super().to_representation(instance)
        # Ensure decimals are serialized as numbers for the frontend.
        rep['amount'] = float(rep['amount']) if rep.get('amount') is not None else None
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
    """Serialize an event with nested participants and expenses (read-only)."""
    participants = ParticipantSerializer(many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'participants', 'expenses']
class CategorySerializer(serializers.ModelSerializer):
    """Serialize an expense category (id, name)."""
    class Meta:
        model = Category
        fields = ['id', 'name']