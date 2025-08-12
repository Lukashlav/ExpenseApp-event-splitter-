import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def get_balance(self):
        """
        Vrací dict {participant_id: balance}
        Kladná hodnota = má dostat peníze, záporná = dluží.
        """
        balances = {p.id: 0 for p in self.participants.all()}

        for expense in self.expenses.all():
            split_count = expense.split_between.count()
            if split_count == 0:
                continue

            share = expense.amount / split_count

            for participant in expense.split_between.all():
                balances[participant.id] -= share

            balances[expense.payer.id] += expense.amount

        return balances
    
    def get_settlement(self):
        """
        Vrátí seznam plateb, které vyrovnají dluhy.
        Výstup je list dictů: {"from": participant_name, "to": participant_name, "amount": Decimal}
        """

        balances = self.get_balance()
        # převod na seznam (participant_id, balance)
        creditors = []
        debtors = []

        for participant, amount in balances.items():
            amt = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if amt > 0:
                creditors.append([participant, amt])
            elif amt < 0:
                debtors.append([participant, -amt])  # záporná hodnota → dluh

        settlements = []

        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debtor, debt_amt = debtors[i]
            creditor, cred_amt = creditors[j]
            payment = min(debt_amt, cred_amt)
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
    event = models.ForeignKey(Event, related_name="participants", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.event.title})"

class Expense(models.Model):
    event = models.ForeignKey(Event, related_name="expenses", on_delete=models.CASCADE)
    payer = models.ForeignKey(Participant, related_name="paid_expenses", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    split_between = models.ManyToManyField(Participant, related_name="splits", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.amount} ({self.event.title})"