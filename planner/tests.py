from django.test import TestCase
# Add necessary imports for the tests
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse

from .forms import ExpenseForm
from .models import Budget, Expense, Income, Profile


class PlannerViewsTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="alex", password="Strong-pass-123")
		self.other_user = User.objects.create_user(username="other", password="Strong-pass-123")

	def test_registration_logs_user_in(self):
		response = self.client.post(reverse("register"), {
			"username": "new-user",
			"email": "new@example.com",
			"password1": "Strong-pass-123",
			"password2": "Strong-pass-123",
		})
		self.assertRedirects(response, reverse("dashboard"))
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_valid_login_redirects_to_dashboard(self):
		response = self.client.post(reverse("login"), {
			"username": "alex",
			"password": "Strong-pass-123",
		})
		self.assertRedirects(response, reverse("dashboard"))
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_dashboard_aggregates_only_current_users_records(self):
		Income.objects.create(user=self.user, source="Salary", amount=Decimal("5000.00"), date=date.today())
		Expense.objects.create(user=self.user, description="Rent", category="Housing", amount=Decimal("1200.00"), date=date.today())
		Income.objects.create(user=self.other_user, source="Private", amount=Decimal("9999.00"), date=date.today())
		self.client.force_login(self.user)

		response = self.client.get(reverse("dashboard"))

		self.assertEqual(response.context["total_income"], Decimal("5000.00"))
		self.assertEqual(response.context["total_expenses"], Decimal("1200.00"))
		self.assertEqual(response.context["balance"], Decimal("3800.00"))
		self.assertContains(response, "₹5000.00")

	def test_anonymous_user_is_redirected_from_private_pages(self):
		response = self.client.get(reverse("dashboard"))
		self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

	def test_user_cannot_edit_or_delete_another_users_expense(self):
		expense = Expense.objects.create(
			user=self.other_user,
			description="Private",
			amount=Decimal("10.00"),
			date=date.today(),
		)
		self.client.force_login(self.user)

		edit_response = self.client.get(reverse("transaction_edit", args=["expense", expense.pk]))
		delete_response = self.client.post(reverse("transaction_delete", args=["expense", expense.pk]))

		self.assertEqual(edit_response.status_code, 404)
		self.assertEqual(delete_response.status_code, 404)
		self.assertTrue(Expense.objects.filter(pk=expense.pk).exists())

	def test_logout_requires_post(self):
		self.client.force_login(self.user)
		self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
		self.assertRedirects(self.client.post(reverse("logout")), reverse("home"))

	def test_negative_amount_is_rejected_by_model_validation(self):
		form = ExpenseForm(data={
			"description": "Invalid",
			"category": "Other",
			"amount": "-1.00",
			"date": date.today().isoformat(),
		})
		self.assertFalse(form.is_valid())
		self.assertIn("amount", form.errors)

	def test_duplicate_email_is_rejected(self):
		self.user.email = "alex@example.com"
		self.user.save(update_fields=["email"])
		response = self.client.post(reverse("register"), {
			"username": "another-user",
			"email": "ALEX@example.com",
			"password1": "Strong-pass-123",
			"password2": "Strong-pass-123",
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "already exists")

	def test_login_rejects_external_next_url(self):
		response = self.client.post(reverse("login") + "?next=//evil.example", {
			"username": "alex",
			"password": "Strong-pass-123",
			"next": "//evil.example",
		})
		self.assertRedirects(response, reverse("dashboard"))

	def test_budget_is_created_for_current_user_and_normalizes_month(self):
		self.client.force_login(self.user)
		response = self.client.post(reverse("budgets"), {
			"category": "Food",
			"month": "2026-09",
			"amount": "800",
		})
		self.assertRedirects(response, reverse("budgets"))
		budget = Budget.objects.get(user=self.user)
		self.assertEqual(budget.month.day, 1)
		self.assertFalse(Budget.objects.filter(user=self.other_user).exists())

	def test_profile_page_creates_missing_profile_for_existing_user(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("profile"))
		self.assertEqual(response.status_code, 200)
		self.assertTrue(Profile.objects.filter(user=self.user).exists())

	def test_unknown_transaction_kind_returns_not_found(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse("transaction_edit", args=["unknown", 1]))
		self.assertEqual(response.status_code, 404)

# Create your tests here.
