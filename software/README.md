
### Retail Management & Repair Service Desktop Application

**A Python-based desktop solution for electrical retail operations, billing, inventory control, sales reporting, and repair-service workflows.**


## Overview

**ElectroSmart** is a desktop retail management application designed to simplify everyday operations for an electrical and electronics business. It brings together point-of-sale billing, product and stock management, sales history, reporting, and a dedicated repairing and maintenance workflow in one application.

The project demonstrates practical desktop application development, relational database design, transaction-oriented workflows, input validation, and PDF document generation.

> **Project status:** Core application development is complete. Windows executable packaging and installer distribution are in progress. The repository currently provides the Python source code.

## Key Features

| Module | Capabilities |
| **Point of Sale (POS)** | Search products, build a cart, adjust quantities and prices, apply discounts, select payment methods, and generate bills. |
| **Products & Inventory** | Maintain product details, purchase and selling prices, stock quantities, and minimum-stock thresholds. |
| **Sales History** | Review past transactions, search invoices, inspect sale details, edit sales, and open or print invoices. |
| **Reports** | View sales summaries, payment-method breakdowns, low-stock items, and top-selling products; export reports as PDF. |
| **Repairing & Maintenance** | Register repair jobs, record faults, prepare estimates, manage approval and repair statuses, and create final bills. |
| **PDF Billing** | Generate invoices and repair documents, with support for different paper sizes in the POS workflow. |

### Repair Service Workflow

```text
Receive Customer Item
        ↓
Register Repair Job
        ↓
Prepare Raw Estimate
        ↓
Customer Decision
   ├── Rejected → Close / Update Job
   └── Approved
          ↓
      Repair Work
          ↓
      Actual Bill
          ↓
      Delivery
```

Repair statuses include **Pending Approval**, **Approved**, **Rejected**, **In Repair**, **Ready for Delivery**, **Delivered**, and **Cancelled**.

## Tech Stack

| Technology | Purpose |
| **Python** | Core application logic |
| **PySide6 (Qt)** | Desktop user interface |
| **SQLite** | Local relational database |
| **ReportLab** | PDF invoices and reports |
| **QtAwesome** | Interface icons |



### 1. Clone the Repository

```bash
git clone https://github.com/aleenafatima4156-crypto/ElectroSmart-Retail-Management-System.git
cd ElectroSmart-Retail-Management-System/software
```

### 2. Create a Virtual Environment

```powershell
python -m venv venv
```

Activate it in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

```cmd
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

> **Note:** The Windows `.exe` installer is not yet included. Run the application from Python using the instructions above. Check the code and configuration before using real customer data.


## Engineering Highlights

- Modular application organization with separate UI and database responsibilities.
- SQLite-backed product, sales, and repair-related records.
- Stock updates linked to completed sales and sale editing.
- Validation and error handling for important application workflows.
- PDF generation for invoices, estimates, and reports.
- Business-focused interface designed around daily retail operations.


## Intended Use

This project is a **portfolio and desktop software development project**. It is intended to demonstrate practical Python application development for retail and repair-service management. Production deployment should include independent testing, backups, and review of customer-data handling.

## Developer

**Aleena Fatima**  
Python Developer | AI/ML & Desktop Application Development

[GitHub Profile](https://github.com/aleenafatima4156-crypto)

**Built with Python, PySide6, SQLite, and ReportLab.**