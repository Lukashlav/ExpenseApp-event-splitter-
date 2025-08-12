from django.contrib import admin
from .models import Event, Participant, Expense

class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1

class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    inlines = [ParticipantInline, ExpenseInline]

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "event", "created_at")
    list_filter = ("event",)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "payer", "event", "created_at")
    list_filter = ("event", "payer")