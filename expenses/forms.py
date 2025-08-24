from django import forms
from .models import Event, Participant, Expense

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description"]

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ["name", "email"]

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["description", "amount", "payer", "event", "split_between", "category"]