from django.contrib import admin
from .models import Budget, Expense, Income, Profile

# Register your models here.

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
	list_display = ["source", "user", "amount", "date"]
	list_filter = ["date"]
	search_fields = ["source", "user__username"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
	list_display = ["description", "category", "user", "amount", "date"]
	list_filter = ["category", "date"]
	search_fields = ["description", "user__username"]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
	list_display = ["category", "user", "month", "amount"]
	list_filter = ["category", "month"]
	search_fields = ["user__username"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ["user", "currency", "monthly_income_target", "monthly_savings_target"]
	search_fields = ["user__username", "user__email"]