# 🍋 Little Lemon Restaurant - Backend API

A **Django REST Framework (DRF)** backend API for the **Little Lemon Restaurant** project. This API enables customers to browse food items, view the item of the day, and place orders. Managers can manage menu items and orders, while delivery crew members can view and update assigned deliveries.

---

## 🚀 Features

- **Customer Features**:
  - Browse menu items
  - View the item of the day
  - Place orders

- **Manager Features**:
  - Manage menu items
  - Assign delivery crew to orders
  - Monitor order status

- **Delivery Crew Features**:
  - View assigned deliveries
  - Update order status when delivered

---

## 🛠 Tech Stack

- **Python 3.10+**
- **Django 4.x**
- **Django REST Framework**
- **Pipenv** to create a virtual environment
- SQLite (default)

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/little-lemon-api.git
cd little-lemon-api
```

### 2. Install dependencies
```bash
pipenv shell
pipenv install
```

### 3. Apply migrations & create superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the server
```bash
python manage.py runserver
```

## 🔑 API Endpoints (Not the full list, TBD)

| Endpoint                  | Method | Description                     |
|---------------------------|--------|---------------------------------|
| `/api/menu/`             | GET    | List menu items               |
| `/api/orders/`           | POST   | Place an order                |
| `/api/orders/{id}/`      | PATCH  | Update order status           |
| `/api/item-of-the-day/`  | GET    | Get item of the day           |

*(Add full API documentation if available or include Postman collection link)*

---

## 📄 License
This project is licensed under the MIT License.

---
