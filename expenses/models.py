"""
Models for the ExpenseApp application.
Defines entities for categories, events, participants, expenses, and settlements.
"""
from django.db import models
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

    def __str__(self):
        """Return human-readable string representation of the participant."""
        return f"{self.name} ({self.event.title})"

class Expense(models.Model):
    """Represents a single expense paid by a participant and split among others."""
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payer = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='paid_expenses')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='expenses')
    split_between = models.ManyToManyField(Participant, related_name='shared_expenses', blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return human-readable string representation of the expense."""
        return f"{self.description} - {self.amount} ({self.event.title})"


class Settlement(models.Model):
    """Represents a settlement payment between two participants of an event."""
    event = models.ForeignKey(Event, related_name="settlements", on_delete=models.CASCADE)
    from_participant = models.ForeignKey(Participant, related_name="settlements_from", on_delete=models.CASCADE)
    to_participant = models.ForeignKey(Participant, related_name="settlements_to", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return human-readable string representation of the settlement."""
        return f"{self.from_participant.name} → {self.to_participant.name}: {self.amount} Kč"