# 🚀 Project Setup & Testing Guide

Follow the steps below to set up and run the project, along with running Celery workers and executing test suites.

make sure you have .env file containing following variables

```
DJANGO_SECRET_KEY=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
EMAIL_HOST_PASSWORD=
EMAIL_HOST_USER=
DEFAULT_FROM_EMAIL=
EMAIL_PORT=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
MOCK_PAYMENT_SUCCESS=
```

---

## 📦 Installation

Install all dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 🛠️ Database Setup

Run the following commands to create migrations and apply them:
(**Postgresql database is used for now**)

```bash
python manage.py makemigrations
python manage.py migrate
```

## 🌐 Start the Django Server

```bash
python manage.py runserver
```

## ⚙️ Start Celery Workers

**🔄 Celery Worker**

```bash
celery -A billing_service worker --loglevel=info -P solo
```

**⏰ Celery Beat Scheduler**

```bash
celery -A billing_service beat --loglevel=info
```

**📅 Add 3 Plans before Testing via following command**

```bash
python manage.py add_plans
```

# API Endpoints

Below is the list of available API endpoints with their HTTP methods and descriptions.

| Endpoint                   | Method | Description                                                 |
| -------------------------- | ------ | ----------------------------------------------------------- |
| `/signup/`                 | POST   | Register a new user                                         |
| `/plans/`                  | GET    | Retrieve list of available plans                            |
| `/subscribe/`              | POST   | Subscribe to a plan                                         |
| `/unsubscribe/`            | POST   | Unsubscribe from a plan                                     |
| `/subscriptions/`          | GET    | List all subscriptions for the authenticated user           |
| `/invoice/pay/`            | POST   | Pay an invoice (❌ pay without payment gateway for testing) |
| `/invoices/`               | GET    | List all invoices for the authenticated user                |
| `/invoice/latest/`         | GET    | Get the latest invoice for the authenticated user           |
| `/invoice/create-order/`   | POST   | Create a Razorpay order for an invoice                      |
| `/invoice/verify-payment/` | POST   | Verify Razorpay payment and update invoice status           |

---

### Notes:

- All endpoints except `/signup/` require authentication (JWT Bearer token).
- For payment-related endpoints, Razorpay integration is used.

---

## Celery Tasks for Subscription and Invoice Management

This project uses the following Celery tasks to automate subscription billing and invoice management:

### 1. `generate_daily_invoice`

- Runs daily to create new invoices for active subscriptions based on their billing cycle.
- Checks each active subscription to determine if today is the start of a new billing cycle.
- If so, it generates an unpaid invoice for the billing period.
- Ensures no duplicate invoices are created for the same billing cycle.

### 2. `mark_overdue_invoices`

- Runs periodically to check all unpaid invoices past their due date.
- Marks such invoices as `overdue`.
- If an invoice has been overdue for more than 7 days, it cancels the corresponding subscription.

### 3. `send_invoice_reminders` (✅bonus feature)

- Sends email reminders for invoices that are overdue but whose subscriptions are still active.
- Uses an asynchronous task to send subscription overdue notification emails.
- Logs reminders sent for each overdue invoice.

---

# 😎 BONUS Features

- **Actual Email Reminder be sent if invoice is unpaid.**
- **Razorpay payment gateway added. (while testing mocking the successful and failed payments)**

---

# 🧪 TEST COVERAGE

#### 🔐 Auth All tests use JWT authentication with `Bearer` tokens.

## ✅ Model Unit Tests

This test suite ensures the correct creation and behavior of core models in the system.

### ✔️ Covered Models:

- **MyUser**: Verifies custom user creation with username and email.
- **Plan**: Validates basic plan fields including name, price, duration, and timestamps.
- **Subscription**: Ensures subscriptions are created with correct start and end dates based on plan duration.
- **Invoice**: Tests invoice creation, due dates, and billing period calculations.

### 🧪 How to Run

```bash
python manage.py test api.tests.integration_test
```

## ✅ Authentication API Tests

These tests ensure that user registration and login APIs are functioning correctly.

- **User Registration**

  - Registers a user with valid credentials.
  - Handles invalid input (e.g., bad email format).

- **User Login**
  - Successfully logs in with correct credentials.
  - Fails login with incorrect password.

### 🧪 How to Run

```bash
python manage.py test api.tests.api_test.auth_test
```

## ✅ API Integration Tests (Subscription & Plan)

These tests ensure correct functionality of the subscription and plan-related APIs.

---

### Plan Tests

- **GET /api/plans/**
  - Returns only active plans.

---

### Subscription Tests

- **POST /api/subscribe/**

  - Allows authenticated users to subscribe to active plans.
  - Creates related `Subscription` and `Invoice`.
  - Prevents multiple active subscriptions for the same user.

- **POST /api/unsubscribe/**

  - Allows users to cancel their subscription.
  - Updates status to `cancelled`.

- **GET /api/subscriptions/**
  - Lists all subscriptions for the authenticated user (active and past).

---

### 🧪 How to Run

```bash
python manage.py test api.tests.api_test.subscription_test
```

## ✅ Invoice API Tests

These test cases verify the correctness and security of invoice-related endpoints, ensuring only authenticated users can access their own invoice data.

---

- **GET /api/invoices/**

  - Lists all invoices for the authenticated user.
  - Returns correct invoice count and IDs.

- **GET /api/invoice/latest/**
  - Returns the most recent invoice for the user based on `issue_date`.
  - Returns 404 with `{ "error": "No invoices found" }` if no invoices exist.

---

## ✅ Razorpay Payment Integration API Tests

These test cases cover the Razorpay-related endpoints for creating orders and verifying payments against invoices.

---

- **POST /api/invoice/create-order/**

  - Creates a Razorpay order for a valid unpaid invoice.
  - Mocks Razorpay API response and updates the invoice with `razorpay_order_id`.
  - Returns `400 Bad Request` with `{ "error": "Invoice not found or already paid" }` for invalid or paid invoices.

- **POST /api/invoice/verify-payment/**

  - Marks invoice as paid if Razorpay payment verification is successful.

  - Returns 400 Bad Request with `{ "error": "Invalid signature" }` if verification fails.

### 🧪 How to Run

```bash
python manage.py test api.tests.api_test.payment_test
```

---

## ✅ Celery Task Functionality Tests

These test cases cover the behavior of asynchronous background tasks used for invoicing and subscription management.

---

- **`generate_daily_invoice()`**

  - Generates an invoice for active subscriptions when the current billing cycle ends.
  - Mocks the current date to simulate invoice generation after the subscription start.
  - Verifies that a new unpaid invoice is created.

- **`mark_overdue_invoices()`**

  - Updates status of invoices past their due date from `unpaid` to `overdue`.
  - Ensures correct invoice status update logic.

- **`mark_overdue_invoices()` with subscription cancellation**

  - If the invoice is overdue and a grace period has passed, the related subscription is cancelled.
  - Verifies both invoice status and subscription status updates.

- **`send_invoice_reminders()`**

  - Sends reminder emails for overdue invoices using a Celery task.
  - Mocks the email sending task to verify the reminder is triggered only for overdue invoices.

---

### 🧪 How to Run

```bash
python manage.py test api.tests.celery_test
```

---

## ✅Postman Collection link for API Testing

[Billing Service Collection](https://www.postman.com/interstellar-desert-4342-1/workspace/billing-service/collection/7249639-0fc4ec14-19bc-4238-80ef-f52a2577d157?action=share&source=copy-link&creator=7249639)
