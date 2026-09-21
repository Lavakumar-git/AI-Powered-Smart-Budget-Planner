from django.urls import path
from django.contrib.auth import views as auth_views
from .views import assistant, budget_delete, budgets, dashboard, expense_create, home, income_create, login_view, logout_view, notifications, password_change, profile, register, settings_view, transaction_delete, transaction_edit, transactions

urlpatterns = [
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("register/", register, name="register"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="password_reset.html", email_template_name="password_reset_email.txt"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), name="password_reset_complete"),
    path("password-change/", password_change, name="password_change"),
    path("dashboard/", dashboard, name="dashboard"),
    path("budgets/", budgets, name="budgets"),
    path("budgets/<int:pk>/delete/", budget_delete, name="budget_delete"),
    path("assistant/", assistant, name="assistant"),
    path("profile/", profile, name="profile"),
    path("settings/", settings_view, name="settings"),
    path("transactions/", transactions, name="transactions"),
    path("income/add/", income_create, name="income_add"),
    path("expenses/add/", expense_create, name="expense_add"),
    path("transactions/<str:kind>/<int:pk>/edit/", transaction_edit, name="transaction_edit"),
    path("transactions/<str:kind>/<int:pk>/delete/", transaction_delete, name="transaction_delete"),
    path("notifications/", notifications, name="notifications"),
    path("logout/", logout_view, name="logout"),
]