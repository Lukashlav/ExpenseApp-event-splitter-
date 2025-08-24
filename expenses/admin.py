from django.contrib import admin
from .models import Event, Participant, Expense, Settlement, Category

class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 1

class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title",)
    date_hierarchy = "created_at"
    inlines = [ParticipantInline, ExpenseInline]

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "event", "created_at")
    list_filter = ("event",)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "payer", "event", "category", "created_at")
    list_filter = ("event", "category")
    search_fields = ("description",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("event", "from_participant", "to_participant", "amount", "created_at")