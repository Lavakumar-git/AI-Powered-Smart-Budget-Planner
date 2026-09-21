from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incomes")
    source = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["user", "-date"])]
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="income_amount_positive")]

    def __str__(self):
        return f"{self.source} - ₹{self.amount}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ("Housing", "Housing"),
        ("Food", "Food"),
        ("Transport", "Transport"),
        ("Health", "Health"),
        ("Entertainment", "Entertainment"),
        ("Shopping", "Shopping"),
        ("Bills", "Bills"),
        ("Other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    description = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="Other")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["user", "-date"])]
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name="expense_amount_positive")]

    def __str__(self):
        return f"{self.description} - ₹{self.amount}"


class Profile(models.Model):
    CURRENCY_CHOICES = [("INR", "Indian Rupee (₹)"), ("USD", "US Dollar ($)"), ("EUR", "Euro (€)")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="INR")
    monthly_income_target = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    monthly_savings_target = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    category = models.CharField(max_length=30, choices=Expense.CATEGORY_CHOICES)
    month = models.DateField(help_text="Use the first day of the budget month.")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-month", "category"]
        constraints = [
            models.UniqueConstraint(fields=["user", "category", "month"], name="unique_user_category_budget_month"),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="budget_amount_positive"),
        ]
        indexes = [models.Index(fields=["user", "month"])]

    def clean(self):
        if self.month.day != 1:
            raise ValidationError({"month": "Budget month must be the first day of a month."})

    def __str__(self):
        return f"{self.category} - {self.month:%B %Y}"