from decimal import Decimal
from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import BudgetForm, ExpenseForm, IncomeForm, LoginForm, ProfileForm, RegisterForm
from .models import Budget, Expense, Income, Profile

from google import genai
from django.conf import settings


def home(request):
    return render(request, "home.html")


def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect("dashboard")
    return render(request, "login.html", {"form": form, "next": request.GET.get("next", "")})


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to SmartBudget!")
        return redirect("dashboard")
    return render(request, "register.html", {"form": form})


def _save_owned_form(request, form_class, model_class, template_name, title, pk=None):
    instance = get_object_or_404(model_class, pk=pk, user=request.user) if pk else None
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.user = request.user
        record.save()
        messages.success(request, f"{title} saved successfully.")
        return redirect("transactions")
    return render(request, template_name, {"form": form, "title": title})


@login_required(login_url="login")
def income_create(request):
    return _save_owned_form(request, IncomeForm, Income, "transaction_form.html", "Add income")


@login_required(login_url="login")
def expense_create(request):
    return _save_owned_form(request, ExpenseForm, Expense, "transaction_form.html", "Add expense")


@login_required(login_url="login")
def transaction_edit(request, kind, pk):
    transaction_types = {"income": (Income, IncomeForm, "Edit income"), "expense": (Expense, ExpenseForm, "Edit expense")}
    if kind not in transaction_types:
        return render(request, "404.html", status=404)
    model_class, form_class, title = transaction_types[kind]
    return _save_owned_form(request, form_class, model_class, "transaction_form.html", title, pk)


@require_POST
@login_required(login_url="login")
def transaction_delete(request, kind, pk):
    if kind not in {"income", "expense"}:
        return render(request, "404.html", status=404)
    model_class = {"income": Income, "expense": Expense}[kind]
    record = get_object_or_404(model_class, pk=pk, user=request.user)
    record.delete()
    messages.success(request, "Transaction deleted.")
    return redirect("transactions")


@login_required(login_url="login")
def transactions(request):
    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)
    rows = [{"record": income, "kind": "income", "label": income.source} for income in incomes]
    rows += [{"record": expense, "kind": "expense", "label": expense.description} for expense in expenses]
    rows.sort(key=lambda row: (row["record"].date, row["record"].created_at), reverse=True)
    return render(request, "transactions.html", {"transactions": rows})


@login_required(login_url="login")
def dashboard(request):
    selected_month = request.GET.get("month", "")
    try:
        year, month = (int(value) for value in selected_month.split("-"))
        period_start = date(year, month, 1)
    except (TypeError, ValueError):
        today = timezone.localdate()
        period_start = today.replace(day=1)
        selected_month = period_start.strftime("%Y-%m")
    next_month = date(period_start.year + (period_start.month == 12), (period_start.month % 12) + 1, 1)
    incomes = Income.objects.filter(user=request.user, date__gte=period_start, date__lt=next_month)
    expenses = Expense.objects.filter(user=request.user, date__gte=period_start, date__lt=next_month)
    total_income = incomes.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    balance = total_income - total_expenses
    savings_rate = (balance / total_income * 100) if total_income else Decimal("0")
    recent_transactions = list(incomes[:10]) + list(expenses[:10])
    recent_transactions.sort(key=lambda item: (item.date, item.created_at), reverse=True)
    return render(request, "dashboard.html", {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "savings_rate": savings_rate,
        "category_totals": expenses.values("category").annotate(total=Sum("amount")).order_by("-total"),
        "recent_transactions": recent_transactions[:5],
        "selected_month": selected_month,
        "budget_total": Budget.objects.filter(user=request.user, month=period_start).aggregate(total=Sum("amount"))["total"] or Decimal("0"),
        "monthly_budget_count": Budget.objects.filter(user=request.user, month=period_start).count(),
    })


@login_required(login_url="login")
def profile(request):
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=user_profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile settings saved.")
        return redirect("profile")
    return render(request, "profile.html", {"form": form})


@login_required(login_url="login")
def password_change(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Your password was changed successfully.")
        return redirect("settings")
    return render(request, "password_change.html", {"form": form})


@login_required(login_url="login")
def settings_view(request):
    return render(request, "settings.html")


@login_required(login_url="login")
def budgets(request):
    form = BudgetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        budget = form.save(commit=False)
        budget.user = request.user
        try:
            budget.save()
        except Exception:
            form.add_error(None, "A budget for this category and month already exists.")
        else:
            messages.success(request, "Budget saved successfully.")
            return redirect("budgets")
    rows = []
    for budget in Budget.objects.filter(user=request.user):
        spent = Expense.objects.filter(user=request.user, category=budget.category, date__year=budget.month.year, date__month=budget.month.month).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        rows.append({"budget": budget, "spent": spent, "remaining": budget.amount - spent})
    return render(request, "budgets.html", {"form": form, "budget_rows": rows})


@require_POST
@login_required(login_url="login")
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    messages.success(request, "Budget deleted.")
    return redirect("budgets")


@login_required(login_url="login")
def assistant(request):

    today = timezone.localdate()
    month_start = today.replace(day=1)

    income = (
        Income.objects
        .filter(
            user=request.user,
            date__gte=month_start
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=month_start
    )

    total_expenses = (
        expenses
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    savings = income - total_expenses

    top_category = (
        expenses
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
        .first()
    )

    if top_category:
        top_category_name = top_category["category"]
        top_category_amount = top_category["total"]
    else:
        top_category_name = "No expenses recorded"
        top_category_amount = Decimal("0")

    insights = []

    if not settings.GEMINI_API_KEY:

        insights.append(
            "Gemini AI is not configured yet."
        )

    else:

        try:

            client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

            financial_summary = f"""
Monthly financial summary:

Income: ₹{income:.2f}
Expenses: ₹{total_expenses:.2f}
Savings/Balance: ₹{savings:.2f}
Largest spending category: {top_category_name}
Amount spent in largest category: ₹{top_category_amount:.2f}
"""

            prompt = f"""
You are the AI Financial Assistant inside SmartBudget,
a personal budgeting application.

Analyze this user's current-month financial data:

{financial_summary}

Provide exactly 3 short, practical financial insights.

Rules:
- Use the actual numbers provided.
- Do not invent financial data.
- Focus on spending, saving, and budgeting.
- Keep each insight to 1 or 2 sentences.
- Be clear, helpful, and encouraging.
- Do not provide investment, tax, or legal advice.
- Return only the 3 insights as separate lines.
- Do not use headings.
"""

            interaction = client.interactions.create(
                model="gemini-3.6-flash",
                input=prompt
            )

            ai_text = interaction.output_text.strip()

            insights = [
                line.strip("-• ")
                for line in ai_text.splitlines()
                if line.strip()
            ]

        except Exception as error:

            print("AI error:", error)

            insights = [
                "AI insights are temporarily unavailable.",
                "Please try again in a moment.",
            ]

    return render(
        request,
        "assistant.html",
        {
            "insights": insights,
            "income": income,
            "expenses": total_expenses,
        }
    )

@login_required(login_url="login")
def notifications(request):

    today = timezone.localdate()

    # Current month
    current_month_start = today.replace(day=1)

    # Previous month
    if current_month_start.month == 1:
        previous_month_start = date(
            current_month_start.year - 1,
            12,
            1
        )
    else:
        previous_month_start = date(
            current_month_start.year,
            current_month_start.month - 1,
            1
        )

    current_month_end = date(
        current_month_start.year + (
            current_month_start.month == 12
        ),
        (current_month_start.month % 12) + 1,
        1
    )

    current_month_income = (
        Income.objects
        .filter(
            user=request.user,
            date__gte=current_month_start,
            date__lt=current_month_end
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    current_month_expenses = (
        Expense.objects
        .filter(
            user=request.user,
            date__gte=current_month_start,
            date__lt=current_month_end
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    current_balance = (
        current_month_income - current_month_expenses
    )

    previous_month_income = (
        Income.objects
        .filter(
            user=request.user,
            date__gte=previous_month_start,
            date__lt=current_month_start
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    previous_month_expenses = (
        Expense.objects
        .filter(
            user=request.user,
            date__gte=previous_month_start,
            date__lt=current_month_start
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    previous_balance = (
        previous_month_income - previous_month_expenses
    )

    balance_change = current_balance - previous_balance

    notifications_list = []

    if current_balance < previous_balance:

        notifications_list.append({
            "type": "warning",
            "icon": "fa-arrow-trend-down",
            "title": "Balance is decreasing",
            "message": (
                f"Your balance has decreased by "
                f"₹{abs(balance_change):.2f} compared with last month. "
                "Review your recent spending to keep your finances on track."
            ),
        })

    elif current_balance > previous_balance:

        notifications_list.append({
            "type": "success",
            "icon": "fa-arrow-trend-up",
            "title": "Balance is improving",
            "message": (
                f"Your balance has increased by "
                f"₹{balance_change:.2f} compared with last month. "
                "Keep maintaining your spending discipline."
            ),
        })

    else:

        notifications_list.append({
            "type": "info",
            "icon": "fa-chart-line",
            "title": "Your balance is stable",
            "message": (
                "Your current-month balance is unchanged compared "
                "with the previous month."
            ),
        })

    return render(
        request,
        "notifications.html",
        {
            "notifications": notifications_list,
            "current_balance": current_balance,
            "previous_balance": previous_balance,
            "balance_change": balance_change,
        }
    )

@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")