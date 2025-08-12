import uuid
from decimal import Decimal
from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

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