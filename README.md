# Billing & Inventory Management System

A Django REST API for managing products, customers, orders, and generating sales reports with role-based access control.

---

## Features

- **User Roles**: Staff and Manager with different permissions
- **Customer Management**: CRUD operations with soft delete
- **Inventory Management**: Product tracking with automatic stock updates
- **Order Processing**: Multi-item orders with automatic inventory deduction
- **Audit Logging**: Automatic tracking of price and stock changes
- **Low Stock Alerts**: Identify products below minimum stock level
- **Invoice Generation**: PDF invoices for orders
- **Reports**: Sales summary and dashboard statistics
- **Search & Filtering**: Advanced search across customers and orders

---

## Tech Stack

- **Backend**: Django 5.x, Django REST Framework
- **Authentication**: Djoser with Token Authentication
- **Database**: SQLite (default)
- **PDF Generation**: ReportLab
- **Excel Export**: openpyxl
- **Filtering**: django-filter

---

## Installation

### 1. Clone/Download Project
```bash
cd "D:\Raktch tech & soft\billing system"
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install django
pip install djangorestframework
pip install djoser
pip install django-filter
pip install reportlab
pip install openpyxl
pip install pillow
```

### 4. Configure Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run Server
```bash
python manage.py runserver
```

**Server runs at:** `http://127.0.0.1:8000/`

---

## Project Structure
```
billing_system/
├── accounts/          # User authentication
├── customers/         # Customer management
├── inventory/         # Products and audit logs
├── sales/            # Orders and reports
└── core/             # Main settings
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/auth/users/` | Register new user | Public |
| POST | `/auth/token/login/` | Login (get token) | Public |
| POST | `/auth/token/logout/` | Logout | Authenticated |
| GET | `/accounts/me/` | Current user info | Authenticated |

### Customers

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/customers/` | List all customers | Staff/Manager |
| POST | `/customers/` | Create customer | Staff/Manager |
| GET | `/customers/{id}/` | Customer detail | Staff/Manager |
| PUT | `/customers/{id}/` | Update customer | Staff/Manager |
| DELETE | `/customers/{id}/` | Soft delete | Staff/Manager |

**Search:** `GET /customers/?search=Ahmed`

### Products

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/inventory/products/` | List products | Staff/Manager |
| POST | `/inventory/products/` | Create product | Manager only |
| GET | `/inventory/products/{id}/` | Product detail | Staff/Manager |
| PUT | `/inventory/products/{id}/` | Update product | Manager only |
| DELETE | `/inventory/products/{id}/` | Soft delete | Manager only |
| GET | `/inventory/products/low_stock/` | Low stock products | Staff/Manager |

**Search:** `GET /inventory/products/?search=Pen`

**Note:** Staff cannot see `purchase_price` or `profit_margin`.

### Audit Logs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/inventory/audit-logs/` | All audit logs | Manager only |
| GET | `/inventory/audit-logs/{id}/` | Single log | Manager only |

**Filter by product:** `GET /inventory/audit-logs/?product=1`

### Orders

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/sales/orders/` | List orders | Staff/Manager |
| POST | `/sales/orders/` | Create order | Staff/Manager |
| GET | `/sales/orders/{id}/` | Order detail | Staff/Manager |
| PUT | `/sales/orders/{id}/` | Update payment status | Staff/Manager |
| DELETE | `/sales/orders/{id}/` | Delete order | Manager only |
| GET | `/sales/orders/{id}/invoice-pdf/` | Download PDF invoice | Staff/Manager |
| GET | `/sales/orders/export/` | Export sales report (CSV) | Staff/Manager |

**Search:** `GET /sales/orders/?search=Ahmed` (by customer name, phone, or invoice ID)

**Filter:** `GET /sales/orders/?payment_status=paid&start_date=2025-01-01&end_date=2025-12-31`

### Dashboard

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/sales/dashboard/stats/` | Daily statistics | Staff/Manager |

**Staff sees:** Total sales, pending orders  
**Manager sees:** Total sales, pending orders, **total profit**

---

## Testing Guide (Postman)

### 1. Register Manager

**POST** `/auth/users/`
```json
{
    "username": "manager1",
    "password": "manager123",
    "email": "manager@example.com",
    "phone": "01712345678",
    "role": "manager",
    "first_name": "Sarah",
    "last_name": "Manager"
}
```

### 2. Register Staff

**POST** `/auth/users/`
```json
{
    "username": "staff1",
    "password": "staff123",
    "email": "staff@example.com",
    "phone": "01798765432",
    "role": "staff",
    "first_name": "John",
    "last_name": "Staff"
}
```

### 3. Login

**POST** `/auth/token/login/`
```json
{
    "username": "manager1",
    "password": "manager123"
}
```

**Response:**
```json
{
    "auth_token": "a1b2c3d4e5f6..."
}
```

**Copy the token and add to all future requests:**

**Header:**
```
Authorization: Token a1b2c3d4e5f6...
```

### 4. Create Customer

**POST** `/customers/`  
**Header:** `Authorization: Token <your_token>`
```json
{
    "name": "Mr. Ahmed Rahman",
    "phone": "+880-1712-345678",
    "email": "ahmed@gmail.com",
    "address": "123 Main St, Dhaka"
}
```

### 5. Create Product (Manager only)

**POST** `/inventory/products/`  
**Header:** `Authorization: Token <manager_token>`
```json
{
    "name": "Blue Pen",
    "purchase_price": "5.00",
    "selling_price": "10.00",
    "quantity": 100,
    "min_stock_level": 20
}
```

### 6. Create Order

**POST** `/sales/orders/`  
**Header:** `Authorization: Token <your_token>`
```json
{
    "customer": 1,
    "payment_status": "unpaid",
    "items": [
        {"product": 1, "quantity": 3},
        {"product": 2, "quantity": 2}
    ]
}
```

**After order creation:**
- Inventory automatically decreases
- Invoice ID auto-generated (e.g., `INV-2025-0001`)
- Total amount calculated automatically

### 7. Download Invoice

**GET** `/sales/orders/1/invoice-pdf/`  
**Header:** `Authorization: Token <your_token>`

**Response:** PDF file downloads

### 8. Get Dashboard Stats

**GET** `/sales/dashboard/stats/`  
**Header:** `Authorization: Token <manager_token>`

**Response:**
```json
{
    "total_sales_today": 150.00,
    "pending_orders": 3,
    "total_profit_today": 45.00
}
```

---

## User Permissions

### Staff Can:
- View products (without purchase price)
- Create/view/update customers
- Create/view/update orders
- View dashboard (without profit)
- Download invoices
- Export reports

### Staff Cannot:
- Create/edit/delete products
- View purchase prices or profit margins
- Delete orders
- View audit logs

### Manager Can:
- Everything Staff can do
- Create/edit/delete products
- View purchase prices and profit
- Delete orders
- View audit logs

---

## Key Features Explained

### 1. Soft Delete
When you delete a customer or product, it's not removed from the database. Instead, `is_active` is set to `False`. This preserves historical order data.

### 2. Automatic Stock Management
When an order is created, product quantities automatically decrease. If insufficient stock, order creation fails.

### 3. Audit Logging
Changes to product prices or stock are automatically logged with timestamp and user who made the change.

### 4. Low Stock Detection
Products with `quantity < min_stock_level` are flagged and accessible via `/inventory/products/low_stock/`

### 5. Invoice Generation
Each order gets a unique invoice ID (format: `INV-YEAR-NUMBER`). PDF invoices can be downloaded.

### 6. Role-Based Data Visibility
Staff see limited product data (no purchase price/profit). Managers see everything.

---

## Common Issues

### "Unable to log in with provided credentials"
Use `username` (not email) for login.

### "This field is required" on product creation
Make sure all fields are provided: `name`, `purchase_price`, `selling_price`, `quantity`, `min_stock_level`.

### 404 on endpoints
Make sure server is running and you're using correct URL format.

### "Insufficient stock" error
Check product quantity before creating order. Use `/inventory/products/low_stock/` to see stock levels.

---

## Database Models

### User
- username, email, password (Django default)
- phone, role (custom fields)

### Customer
- name, phone, email, address
- is_active (for soft delete)

### Product
- name, purchase_price, selling_price
- quantity, min_stock_level
- is_active (for soft delete)

### Order
- invoice_id (auto-generated)
- customer (FK), created_by (FK to User)
- payment_status (paid/unpaid)
- total_amount (calculated)

### OrderItem
- order (FK), product (FK)
- quantity, price (locked at time of sale)

### AuditLog
- product (FK), action (description)
- changed_by (FK to User), timestamp

---

## Development Notes

- Database: SQLite (located at `db.sqlite3`)
- Token never expires (suitable for development)
- CSRF disabled for API endpoints
- Signals fire on product save to create audit logs

---

## Author

**Your Name**  
Assignment Project - Django REST API

---

## License

Educational project - Not for commercial use