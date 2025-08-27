"""
Models for the ExpenseApp application.
Defines entities for categories, events, participants, expenses, and settlements.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
import uuid
from decimal import Decimal, ROUND_HALF_UP

class Category(models.Model):
    """Represents an expense category (e.g., Food, Travel)."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return human-readable string representation of the category."""
        return self.name

class Event(models.Model):
    """Represents an event that groups participants and expenses."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """Return human-readable string representation of the event."""
        return self.title
    
    def get_balance(self):
        """Return a dict mapping participant_id to balance (positive = to receive, negative = owes)."""
        balances = {p.id: 0 for p in self.participants.all()}

        for expense in self.expenses.all():
            if expense.payer is None:
                continue

            participants_to_split = expense.split_between.all()
            if not participants_to_split.exists():
                # Pokud není nikdo ve split_between, rozdělíme výdaj mezi všechny účastníky
                participants_to_split = self.participants.all()

            split_count = participants_to_split.count()
            if split_count == 0:
                continue
            share = expense.amount / split_count

            for participant in participants_to_split:
                balances[participant.id] -= share

            balances[expense.payer.id] += expense.amount

        return balances
    
    def get_settlement(self):
        """Return a list of settlement transactions to balance debts among participants."""
        balances = self.get_balance()
        creditors = []
        debtors = []

        # Načteme všechny účastníky do slovníku pro rychlý lookup
        participants = {p.id: p for p in self.participants.all()}

        for participant_id, amount in balances.items():
            amt = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            participant = participants.get(participant_id)
            if not participant:
                continue  # pokud účastník není, přeskočíme

            if amt > 0:
                creditors.append([participant, amt])
            elif amt < 0:
                debtors.append([participant, -amt])

        settlements = []

        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debtor, debt_amt = debtors[i]
            creditor, cred_amt = creditors[j]
            payment = min(debt_amt, cred_amt)
            if debtor is not None and creditor is not None:
                settlements.append({
                    "from": debtor.name,
                    "to": creditor.name,
                    "amount": float(payment)
                })

            debt_amt -= payment
            cred_amt -= payment

            if debt_amt == 0:
                i += 1
            else:
                debtors[i][1] = debt_amt

            if cred_amt == 0:
                j += 1
            else:
                creditors[j][1] = cred_amt

        return settlements
        

class Participant(models.Model):
    """Represents a participant of an event."""
    event = models.ForeignKey(Event, related_name="participants", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Jméno účastníka nesmí být prázdné."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_participant_name_per_event"),
        ]
        indexes = [
            models.Index(fields=["event"]),
        ]

    def __str__(self):
        """Return human-readable string representation of the participant."""
        return f"{self.name} ({self.event.title})"

class Expense(models.Model):
    """Represents a single expense paid by a participant and split among others."""
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payer = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='paid_expenses')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='expenses')
    split_between = models.ManyToManyField(Participant, related_name='shared_expenses', blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.payer and self.event and self.payer.event_id != self.event_id:
            raise ValidationError({"payer": "Plátce musí patřit do stejné události."})
        if self.pk:  # when instance exists, we can validate current M2M set
            for participant in self.split_between.all():
                if participant.event_id != self.event_id:
                    raise ValidationError({"split_between": "Všichni účastníci ve splitu musí patřit do stejné události."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="expense_amount_gt_0"),
        ]
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        """Return human-readable string representation of the expense."""
        return f"{self.description} - {self.amount} ({self.event.title})"


@receiver(m2m_changed, sender=Expense.split_between.through)
def validate_split_between(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in {"pre_add", "pre_set"} and pk_set:
        # All participants must belong to the same event as the expense
        invalid = model.objects.filter(pk__in=pk_set).exclude(event_id=instance.event_id).exists()
        if invalid:
            raise ValidationError("Účastníci ve splitu musí patřit do stejné události jako výdaj.")

class Settlement(models.Model):
    """Represents a settlement payment between two participants of an event."""
    event = models.ForeignKey(Event, related_name="settlements", on_delete=models.CASCADE)
    from_participant = models.ForeignKey(Participant, related_name="settlements_from", on_delete=models.CASCADE)
    to_participant = models.ForeignKey(Participant, related_name="settlements_to", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.from_participant_id and self.to_participant_id and self.from_participant_id == self.to_participant_id:
            raise ValidationError({"to_participant": "Plátce a příjemce nesmí být stejná osoba."})
        if self.event_id:
            if self.from_participant and self.from_participant.event_id != self.event_id:
                raise ValidationError({"from_participant": "Plátce musí patřit do stejné události."})
            if self.to_participant and self.to_participant.event_id != self.event_id:
                raise ValidationError({"to_participant": "Příjemce musí patřit do stejné události."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="settlement_amount_gt_0"),
            models.CheckConstraint(condition=~models.Q(from_participant=models.F("to_participant")), name="settlement_from_not_to"),
        ]
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        """Return human-readable string representation of the settlement."""
        return f"{self.from_participant.name} → {self.to_participant.name}: {self.amount} Kč"