# SAP Order-to-Cash (O2C) Simulation System

> A full-stack web simulation of the SAP Order-to-Cash business process cycle, built with Python & Streamlit.

---

## Project Overview

This project simulates the **Order-to-Cash (O2C)** end-to-end business process — one of SAP's core SD (Sales & Distribution) module workflows. It covers the complete journey from sales order creation through to payment receipt, with real-time analytics and professional invoice generation.

Developed as part of the **KIIT SAP Project Work** under the guidance of the SAP Functional curriculum.

---

## O2C Process Flow

```
Create Order → Delivery & Goods Issue → Billing (Invoice) → Payment Receipt
```

---

## Features

| Module              | Features                                                              |
|---------------------|-----------------------------------------------------------------------|
| **Customer Master** | Add customers with name, email, phone; duplicate email prevention     |
| **Material Master** | Add materials with price & stock; inventory tracking                  |
| **Sales Order**     | Create orders with live price preview; stock availability check       |
| **Delivery**        | Goods issue with automatic stock deduction; out-of-stock protection   |
| **Billing**         | GST invoice (CGST 9% + SGST 9%); downloadable professional PDF       |
| **Payments**        | Record payment; AR tracking                                          |
| **Dashboard**       | KPI metrics, donut chart, line chart, revenue bars, recent activity   |
| **Order View**      | Filter by status, color-coded badges, CSV export                      |

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Frontend    | Streamlit + Custom CSS  |
| Charts      | Plotly (interactive)    |
| Backend     | Python 3.x              |
| Database    | SQLite3                 |
| PDF         | ReportLab               |

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize the database
```bash
python db_setup.py
```

### 3. Run the application
```bash
streamlit run app.py
```

### 4. Open in browser
```
http://localhost:8501
```

---

## Project Structure

```
sap-o2c-simulation/
│
├── app.py              # Main Streamlit application
├── db_setup.py         # Database initialization script
├── requirements.txt    # Python dependencies
├── o2c.db              # SQLite database (auto-created)
├── invoice_*.pdf       # Generated invoice files
└── README.md           # Project documentation
```

---

## Database Schema

```
customers   → id, name, email (unique), phone
materials   → id, name, price, stock
orders      → id, customer_id, material_id, quantity, total, status, created_at
payments    → id, order_id, amount, paid_at, method
```

---

## Future Improvements

- Multi-item orders (cart-style)
- Email notifications via SMTP
- Role-based login (Sales Rep / Finance / Warehouse)
- SAP BAPI integration for live system connectivity
- Monthly/quarterly financial reports with export to Excel

---

## Author

Shivangi Padhi
B.Tech CSE - KIIT University
SAP Functional Project
Topic: Order-to-Cash (O2C) — Complete Sales Cycle (SAP SD)
