import qtawesome as qta
from PySide6.QtCore import QSize

def icons(button, icon_name, color="#FFFFFF", size=16):
    """Attach a crisp scalable icon without changing existing button behavior."""
    try:
        button.setIcon(qta.icon(icon_name, color=color))
        button.setIconSize(QSize(size, size))
    except Exception:
        pass
    return button

import sys
import os
import sqlite3
import hashlib
import hmac
import secrets
import qtawesome as qta
from datetime import datetime, date

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QDateEdit,
    QGroupBox,
    QScrollArea,
    QCheckBox,
    QInputDialog,
)
from PySide6.QtCore import Qt, QDate, QSettings, QSize
from PySide6.QtGui import QFont

from modules.pos import POSPage
from modules.inventory import InventoryPage
from modules.products import ProductsPage
from modules.sales_history import SalesHistoryPage
from modules.repairing import RepairingPage
from database.database_manager import DatabaseManager



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "electrosmart.db")
SETTINGS_ORG = "ElectroSmart"
SETTINGS_APP = "ElectricalShop"


def db_connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, table_name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def get_table_columns(conn, table_name):
    """Return existing column names for a SQLite table."""
    if not table_exists(conn, table_name):
        return set()

    try:
        return {
            row["name"]
            for row in conn.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
        }
    except Exception:
        return set()


def first_existing_column(columns, candidates):
    """Return the first candidate that exists in columns."""
    for name in candidates:
        if name in columns:
            return name
    return None


def safe_float(value, default=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default

class ReportsPage(QWidget):
    """Professional sales/profit/stock reports using the existing SQLite DB."""

    def __init__(self):
        super().__init__()
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.db = DatabaseManager()
        self.build_ui()
        self.load_report()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("Reports")
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #1E293B;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "View sales, revenue, profit, payment methods and stock information."
        )
        subtitle.setStyleSheet("color: #64748B; font-size: 14px;")
        layout.addWidget(subtitle)

        controls = QFrame()
        controls.setStyleSheet(
            "QFrame { background: white; border-radius: 10px; }"
        )
        controls_layout = QHBoxLayout(controls)

        controls_layout.addWidget(QLabel("From:"))

        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setDisplayFormat("M/d/yyyy")
        controls_layout.addWidget(self.from_date)

        controls_layout.addWidget(QLabel("To:"))

        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("M/d/yyyy")
        controls_layout.addWidget(self.to_date)

        self.report_type = QComboBox()
        self.report_type.addItems(
            [
                "Sales Summary",
                "Payment Methods",
                "Low Stock",
                "Top Products",
            ]
        )
        controls_layout.addWidget(self.report_type)

        refresh_btn = icons(QPushButton('Generate Report'), 'fa5s.chart-line', '#FFFFFF')
        refresh_btn.clicked.connect(self.load_report)
        controls_layout.addWidget(refresh_btn)

        print_btn = icons(QPushButton('Export PDF'), 'fa5s.file-pdf', '#FFFFFF')
        print_btn.clicked.connect(self.export_pdf)
        controls_layout.addWidget(print_btn)

        layout.addWidget(controls)

        self.summary_grid = QGridLayout()
        self.summary_grid.setSpacing(15)
        self.summary_labels = {}

        for i, (key, title_text) in enumerate(
            [
                ("sales", "Sales"),
                ("revenue", "Revenue"),
                ("profit", "Profit"),
                ("orders", "Orders"),
            ]
        ):
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background: white; border-radius: 10px; }"
            )
            card_layout = QVBoxLayout(card)

            lbl_title = QLabel(title_text)
            lbl_title.setStyleSheet("color: #64748B; font-size: 13px;")

            value = QLabel("0")
            value.setStyleSheet(
                "color: #1E293B; font-size: 23px; font-weight: bold;"
            )

            card_layout.addWidget(lbl_title)
            card_layout.addWidget(value)
            self.summary_labels[key] = value

            self.summary_grid.addWidget(card, 0, i)

        layout.addLayout(self.summary_grid)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        layout.addWidget(self.table)

    
    def load_report(self):
        conn = None

        try:
            if self.from_date.date() > self.to_date.date():
                QMessageBox.warning(
                    self,
                    "Invalid Date Range",
                    "The From date cannot be later than the To date.",
                )
                return

            conn = self.db.connect()

            start = (
                self.from_date.date().toString("yyyy-MM-dd")
                + " 00:00:00"
            )
            end = (
                self.to_date.date().toString("yyyy-MM-dd")
                + " 23:59:59"
            )

            sales_exists = table_exists(conn, "sales")
            items_exists = table_exists(conn, "sale_items")
            products_exists = table_exists(conn, "products")

            total_revenue = 0.0
            total_orders = 0
            total_profit = 0.0

            
            if sales_exists:
                sales_columns = get_table_columns(conn, "sales")

                amount_column = first_existing_column(
                    sales_columns,
                    ["total_amount", "grand_total", "total"],
                )

                date_column = first_existing_column(
                    sales_columns,
                    ["created_at", "date", "sale_date"],
                )

                if amount_column and date_column:
                    row = conn.execute(
                        f"""
                        SELECT
                            COALESCE(SUM({amount_column}), 0) AS revenue,
                            COUNT(*) AS orders
                        FROM sales
                        WHERE {date_column} BETWEEN ? AND ?
                        """,
                        (start, end),
                    ).fetchone()

                    total_revenue = safe_float(row["revenue"])
                    total_orders = int(row["orders"] or 0)
      

            if sales_exists and items_exists and products_exists:
                total_profit = self.calculate_profit(
                    conn, start, end
                )

            self.summary_labels["sales"].setText(
                f"Rs. {total_revenue:,.2f}"
            )
            self.summary_labels["revenue"].setText(
                f"Rs. {total_revenue:,.2f}"
            )
            self.summary_labels["profit"].setText(
                f"Rs. {total_profit:,.2f}"
            )
            self.summary_labels["orders"].setText(
                str(total_orders)
            )


            report = self.report_type.currentText()

            if report == "Sales Summary":
                self.sales_summary(conn, start, end)

            elif report == "Payment Methods":
                self.payment_report(conn, start, end)

            elif report == "Low Stock":
                self.low_stock_report(conn)

            else:
                self.top_products_report(conn, start, end)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Report Error",
                "Unable to generate the report.\n\n"
                f"{type(e).__name__}: {e}",
            )

        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
 
    
    def calculate_profit(self, conn, start, end):
        """
        Calculate profit using the actual columns available in the
        current database. Missing optional columns are handled safely.
        """

        sales_columns = get_table_columns(conn, "sales")
        item_columns = get_table_columns(conn, "sale_items")
        product_columns = get_table_columns(conn, "products")

        sales_date = first_existing_column(
            sales_columns,
            ["created_at", "date", "sale_date"],
        )

        product_id = first_existing_column(
            item_columns,
            ["product_id", "product", "productId"],
        )

        quantity = first_existing_column(
            item_columns,
            ["quantity", "qty"],
        )

        sale_price = first_existing_column(
            item_columns,
            ["price", "selling_price", "unit_price"],
        )

        purchase_price = first_existing_column(
            product_columns,
            ["purchase_price", "cost_price", "buy_price"],
        )

        if not sales_date or not product_id or not quantity:
            return 0.0

        if not purchase_price:

            return 0.0

        if not sale_price:
            sale_price = None

        if sale_price:
            price_expression = (
                f"COALESCE(si.{sale_price}, 0)"
            )
        else:
            product_sale_price = first_existing_column(
                product_columns,
                ["selling_price", "sale_price", "price"],
            )

            if not product_sale_price:
                return 0.0

            price_expression = (
                f"COALESCE(p.{product_sale_price}, 0)"
            )

        query = f"""
            SELECT COALESCE(SUM(
                (
                    {price_expression}
                    - COALESCE(p.{purchase_price}, 0)
                )
                * COALESCE(si.{quantity}, 0)
            ), 0) AS profit
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            LEFT JOIN products p ON p.id = si.{product_id}
            WHERE s.{sales_date} BETWEEN ? AND ?
        """

        row = conn.execute(query, (start, end)).fetchone()
        return safe_float(row["profit"])


    def set_table(self, headers, rows):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                item.setTextAlignment(
                    Qt.AlignLeft | Qt.AlignVCenter
                )
                self.table.setItem(r, c, item)

        self.table.resizeRowsToContents()

    def sales_summary(self, conn, start, end):
        if not table_exists(conn, "sales"):
            self.set_table(
                ["Message"],
                [["Sales table not found"]],
            )
            return

        columns = get_table_columns(conn, "sales")

        invoice_column = first_existing_column(
            columns,
            ["invoice_number", "invoice_no", "invoice"],
        )

        customer_column = first_existing_column(
            columns,
            ["customer_name", "customer", "customerName"],
        )

        amount_column = first_existing_column(
            columns,
            ["total_amount", "grand_total", "total"],
        )

        payment_column = first_existing_column(
            columns,
            ["payment_method", "payment", "payment_type"],
        )

        date_column = first_existing_column(
            columns,
            ["created_at", "date", "sale_date"],
        )

        if not amount_column or not date_column:
            self.set_table(
                ["Message"],
                [[
                    "Sales table does not contain the required "
                    "amount/date columns."
                ]],
            )
            return

        invoice_expression = (
            f"COALESCE({invoice_column}, '-')"
            if invoice_column
            else "'-'"
        )

        customer_expression = (
            f"COALESCE({customer_column}, 'Walk-in Customer')"
            if customer_column
            else "'Walk-in Customer'"
        )

        payment_expression = (
            f"COALESCE({payment_column}, 'Cash')"
            if payment_column
            else "'Cash'"
        )

        rows = conn.execute(
            f"""
            SELECT
                {invoice_expression} AS invoice_number,
                {customer_expression} AS customer_name,
                COALESCE({amount_column}, 0) AS total_amount,
                {payment_expression} AS payment_method,
                {date_column} AS created_at
            FROM sales
            WHERE {date_column} BETWEEN ? AND ?
            ORDER BY rowid DESC
            """,
            (start, end),
        ).fetchall()

        self.set_table(
            ["Invoice", "Customer", "Amount", "Payment", "Date"],
            [
                [
                    r["invoice_number"],
                    r["customer_name"],
                    f"Rs. {safe_float(r['total_amount']):,.2f}",
                    r["payment_method"],
                    r["created_at"],
                ]
                for r in rows
            ],
        )


    def payment_report(self, conn, start, end):
        if not table_exists(conn, "sales"):
            self.set_table(
                ["Message"],
                [["Sales table not found"]],
            )
            return

        columns = get_table_columns(conn, "sales")

        amount_column = first_existing_column(
            columns,
            ["total_amount", "grand_total", "total"],
        )

        payment_column = first_existing_column(
            columns,
            ["payment_method", "payment", "payment_type"],
        )

        date_column = first_existing_column(
            columns,
            ["created_at", "date", "sale_date"],
        )

        if not amount_column or not date_column:
            self.set_table(
                ["Message"],
                [[
                    "Sales table does not contain the required "
                    "amount/date columns."
                ]],
            )
            return

        payment_expression = (
            f"COALESCE({payment_column}, 'Cash')"
            if payment_column
            else "'Cash'"
        )

        rows = conn.execute(
            f"""
            SELECT
                {payment_expression} AS method,
                COUNT(*) AS orders,
                COALESCE(SUM({amount_column}), 0) AS amount
            FROM sales
            WHERE {date_column} BETWEEN ? AND ?
            GROUP BY {payment_expression}
            ORDER BY amount DESC
            """,
            (start, end),
        ).fetchall()

        self.set_table(
            ["Payment Method", "Orders", "Total Amount"],
            [
                [
                    r["method"],
                    r["orders"],
                    f"Rs. {safe_float(r['amount']):,.2f}",
                ]
                for r in rows
            ],
        )
   
    def low_stock_report(self, conn):
        if not table_exists(conn, "products"):
            self.set_table(
                ["Message"],
                [["Products table not found"]],
            )
            return

        columns = get_table_columns(conn, "products")

        name_column = first_existing_column(
            columns,
            ["name", "product_name"],
        )

        category_column = first_existing_column(
            columns,
            ["category"],
        )

        brand_column = first_existing_column(
            columns,
            ["brand"],
        )

        stock_column = first_existing_column(
            columns,
            ["stock", "quantity", "qty"],
        )

        min_stock_column = first_existing_column(
            columns,
            ["min_stock", "minimum_stock", "reorder_level"],
        )

        unit_column = first_existing_column(
            columns,
            ["unit", "unit_name"],
        )

        if not stock_column:
            self.set_table(
                ["Message"],
                [["Products table does not contain a stock column."]],
            )
            return

        name_expression = (
            name_column if name_column else "''"
        )
        category_expression = (
            category_column if category_column else "''"
        )
        brand_expression = (
            brand_column if brand_column else "''"
        )
        unit_expression = (
            unit_column if unit_column else "''"
        )

        default_min_stock = safe_float(
            self.settings.value("low_stock_limit", 5),
            5,
        )

        if min_stock_column:
            minimum_expression = (
                f"COALESCE({min_stock_column}, "
                f"{default_min_stock})"
            )
            where_expression = (
                f"COALESCE({stock_column}, 0) <= "
                f"{minimum_expression}"
            )
        else:
            minimum_expression = str(default_min_stock)
            where_expression = (
                f"COALESCE({stock_column}, 0) <= "
                f"{default_min_stock}"
            )

        rows = conn.execute(
            f"""
            SELECT
                {name_expression} AS name,
                {category_expression} AS category,
                {brand_expression} AS brand,
                COALESCE({stock_column}, 0) AS stock,
                {minimum_expression} AS min_stock,
                {unit_expression} AS unit
            FROM products
            WHERE {where_expression}
            ORDER BY stock ASC
            """
        ).fetchall()

        self.set_table(
            ["Product", "Category", "Brand", "Stock", "Minimum", "Unit"],
            [
                [
                    r["name"],
                    r["category"],
                    r["brand"],
                    r["stock"],
                    r["min_stock"],
                    r["unit"],
                ]
                for r in rows
            ],
        )

    def top_products_report(self, conn, start, end):
        if not table_exists(conn, "sale_items"):
            self.set_table(
                ["Message"],
                [["Sale items table not found"]],
            )
            return

        if not table_exists(conn, "sales"):
            self.set_table(
                ["Message"],
                [["Sales table not found"]],
            )
            return

        item_columns = get_table_columns(conn, "sale_items")
        sales_columns = get_table_columns(conn, "sales")
        product_columns = get_table_columns(conn, "products")

        product_id = first_existing_column(
            item_columns,
            ["product_id", "product", "productId"],
        )

        quantity = first_existing_column(
            item_columns,
            ["quantity", "qty"],
        )

        price = first_existing_column(
            item_columns,
            ["price", "selling_price", "unit_price"],
        )

        sales_date = first_existing_column(
            sales_columns,
            ["created_at", "date", "sale_date"],
        )

        product_name = first_existing_column(
            product_columns,
            ["name", "product_name"],
        )

        product_sale_price = first_existing_column(
            product_columns,
            ["selling_price", "sale_price", "price"],
        )

        if not product_id or not quantity or not sales_date:
            self.set_table(
                ["Message"],
                [[
                    "sale_items/sales structure does not contain "
                    "the required product, quantity or date columns."
                ]],
            )
            return

        if not table_exists(conn, "products"):
            self.set_table(
                ["Message"],
                [["Products table not found"]],
            )
            return

        product_expression = (
            f"COALESCE(p.{product_name}, 'Unknown Product')"
            if product_name
            else "'Unknown Product'"
        )

        if price:
            amount_expression = (
                f"COALESCE(si.{price}, 0) * "
                f"COALESCE(si.{quantity}, 0)"
            )
        elif product_sale_price:
            amount_expression = (
                f"COALESCE(p.{product_sale_price}, 0) * "
                f"COALESCE(si.{quantity}, 0)"
            )
        else:
            amount_expression = "0"

        rows = conn.execute(
            f"""
            SELECT
                {product_expression} AS product,
                COALESCE(SUM(si.{quantity}), 0) AS quantity,
                COALESCE(SUM({amount_expression}), 0) AS amount
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            LEFT JOIN products p ON p.id = si.{product_id}
            WHERE s.{sales_date} BETWEEN ? AND ?
            GROUP BY si.{product_id}
            ORDER BY quantity DESC
            LIMIT 50
            """,
            (start, end),
        ).fetchall()

        self.set_table(
            ["Product", "Quantity Sold", "Sales Amount"],
            [
                [
                    r["product"],
                    r["quantity"],
                    f"Rs. {safe_float(r['amount']):,.2f}",
                ]
                for r in rows
            ],
        )

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
            )

            default_name = (
                f"ElectroSmart_Report_"
                f"{self.from_date.date().toString('yyyyMMdd')}_"
                f"{self.to_date.date().toString('yyyyMMdd')}.pdf"
            )

            reports_dir = os.path.join(BASE_DIR, "reports")
            os.makedirs(reports_dir, exist_ok=True)

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Report PDF",
                os.path.join(reports_dir, default_name),
                "PDF Files (*.pdf)",
            )

            if not path:
                return

            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            doc = SimpleDocTemplate(path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            shop_name = self.settings.value(
                "shop_name",
                "Nadeem Shahanvi Electrical & Electronic Care Centre",
            )

            story.append(
                Paragraph(
                    str(shop_name),
                    styles["Title"],
                )
            )
            story.append(
                Paragraph(
                    "Business Report",
                    styles["Heading2"],
                )
            )
            story.append(
                Paragraph(
                    f"Report Type: {self.report_type.currentText()}",
                    styles["Normal"],
                )
            )
            story.append(
                Paragraph(
                    f"Period: "
                    f"{self.from_date.date().toString('dd-MM-yyyy')} "
                    f"to "
                    f"{self.to_date.date().toString('dd-MM-yyyy')}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 15))

            revenue_text = self.summary_labels["revenue"].text()
            profit_text = self.summary_labels["profit"].text()
            orders_text = self.summary_labels["orders"].text()

            story.append(
                Paragraph(
                    f"Revenue: {revenue_text}",
                    styles["Normal"],
                )
            )
            story.append(
                Paragraph(
                    f"Profit: {profit_text}",
                    styles["Normal"],
                )
            )
            story.append(
                Paragraph(
                    f"Orders: {orders_text}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 15))

            headers = []

            for c in range(self.table.columnCount()):
                item = self.table.horizontalHeaderItem(c)
                headers.append(
                    item.text() if item else ""
                )

            data = [headers]

            for r in range(self.table.rowCount()):
                row = []

                for c in range(self.table.columnCount()):
                    item = self.table.item(r, c)
                    row.append(
                        item.text() if item else ""
                    )

                data.append(row)

            if len(data) > 1 and any(headers):
     
                safe_data = []

                for row in data:
                    safe_row = []

                    for value in row:
                        text = str(value)
                        if len(text) > 80:
                            text = text[:77] + "..."
                        safe_row.append(text)

                    safe_data.append(safe_row)

                tbl = Table(
                    safe_data,
                    repeatRows=1,
                    hAlign="LEFT",
                )

                tbl.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor("#1E293B"),
                            ),
                            (
                                "TEXTCOLOR",
                                (0, 0),
                                (-1, 0),
                                colors.white,
                            ),
                            (
                                "GRID",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                colors.grey,
                            ),
                            (
                                "FONTNAME",
                                (0, 0),
                                (-1, 0),
                                "Helvetica-Bold",
                            ),
                            (
                                "FONTSIZE",
                                (0, 0),
                                (-1, -1),
                                8,
                            ),
                            (
                                "VALIGN",
                                (0, 0),
                                (-1, -1),
                                "MIDDLE",
                            ),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [
                                    colors.white,
                                    colors.HexColor("#F8FAFC"),
                                ],
                            ),
                        ]
                    )
                )

                story.append(tbl)

            else:
                story.append(
                    Paragraph(
                        "No records found for this report.",
                        styles["Normal"],
                    )
                )

            doc.build(story)

            QMessageBox.information(
                self,
                "Report Exported",
                f"Report successfully saved:\n\n{path}",
            )

        except ImportError:
            QMessageBox.warning(
                self,
                "ReportLab Required",
                "Report PDF export requires reportlab.\n\n"
                "Install it with:\n\n"
                "pip install reportlab",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                "Could not export the report.\n\n"
                f"{type(e).__name__}: {e}",
            )


class SettingsPage(QWidget):
    """Application/shop settings saved using QSettings."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 25, 30, 25)

        title = QLabel("Settings")
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #1E293B;"
        )
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)

        shop_group = QGroupBox("Shop Information")
        form = QFormLayout(shop_group)

        self.shop_name = QLineEdit()
        self.shop_name.setPlaceholderText("Electrical shop name")

        self.shop_phone = QLineEdit()
        self.shop_phone.setPlaceholderText("Phone number")

        self.shop_address = QLineEdit()
        self.shop_address.setPlaceholderText("Shop address")

        self.currency = QLineEdit()
        self.currency.setPlaceholderText("Rs.")

        form.addRow("Shop Name:", self.shop_name)
        form.addRow("Phone:", self.shop_phone)
        form.addRow("Address:", self.shop_address)
        form.addRow("Currency:", self.currency)

        layout.addWidget(shop_group)

        invoice_group = QGroupBox("Invoice / Printing")
        invoice_form = QFormLayout(invoice_group)

        self.paper_size = QComboBox()
        self.paper_size.addItems(
            [
                "Thermal 80mm",
                "Thermal 58mm",
                "A4",
                "A5",
                "A6",
            ]
        )

        self.logo_path = QLineEdit()

        browse = icons(QPushButton('Browse'), 'fa5s.folder-open', '#FFFFFF')
        browse.clicked.connect(self.browse_logo)

        logo_row = QHBoxLayout()
        logo_row.addWidget(self.logo_path)
        logo_row.addWidget(browse)

        logo_widget = QWidget()
        logo_widget.setLayout(logo_row)

        invoice_form.addRow("Paper Size:", self.paper_size)
        invoice_form.addRow("Invoice Logo:", logo_widget)

        layout.addWidget(invoice_group)

        app_group = QGroupBox("Application")
        app_form = QFormLayout(app_group)

        self.default_payment = QComboBox()
        self.default_payment.addItems(
            [
                "Cash",
                "JazzCash",
                "EasyPaisa",
                "Bank Transfer",
                "Card",
            ]
        )

        self.low_stock_limit = QDoubleSpinBox()
        self.low_stock_limit.setRange(0, 1000000)
        self.low_stock_limit.setDecimals(0)

        app_form.addRow(
            "Default Payment:",
            self.default_payment,
        )
        app_form.addRow(
            "Default Low Stock:",
            self.low_stock_limit,
        )

        layout.addWidget(app_group)

        buttons = QHBoxLayout()

        save_btn = icons(QPushButton('Save Settings'), 'fa5s.save', '#FFFFFF')
        save_btn.clicked.connect(self.save_settings)

        reset_btn = icons(QPushButton('Reset'), 'fa5s.undo', '#FFFFFF')
        reset_btn.clicked.connect(self.load_settings)

        buttons.addWidget(save_btn)
        buttons.addWidget(reset_btn)
        buttons.addStretch()

        layout.addLayout(buttons)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Invoice Logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )

        if path:
            self.logo_path.setText(path)

    def load_settings(self):
        self.shop_name.setText(
            self.settings.value(
                "shop_name",
                "Nadeem Shahanvi Electrical & Electronic Care Centre",
            )
        )

        self.shop_phone.setText(
            self.settings.value("shop_phone", "")
        )

        self.shop_address.setText(
            self.settings.value("shop_address", "")
        )

        self.currency.setText(
            self.settings.value("currency", "Rs.")
        )

        paper_size = self.settings.value(
            "paper_size",
            "Thermal 80mm",
        )

        if self.paper_size.findText(paper_size) < 0:
            paper_size = "Thermal 80mm"

        self.paper_size.setCurrentText(paper_size)

        self.logo_path.setText(
            self.settings.value("logo_path", "")
        )

        self.default_payment.setCurrentText(
            self.settings.value(
                "default_payment",
                "Cash",
            )
        )

        self.low_stock_limit.setValue(
            safe_float(
                self.settings.value(
                    "low_stock_limit",
                    5,
                ),
                5,
            )
        )

    def save_settings(self):
        if not self.shop_name.text().strip():
            QMessageBox.warning(
                self,
                "Shop Name Required",
                "Please enter the shop name.",
            )
            return

        self.settings.setValue(
            "shop_name",
            self.shop_name.text().strip(),
        )

        self.settings.setValue(
            "shop_phone",
            self.shop_phone.text().strip(),
        )

        self.settings.setValue(
            "shop_address",
            self.shop_address.text().strip(),
        )

        self.settings.setValue(
            "currency",
            self.currency.text().strip() or "Rs.",
        )

        self.settings.setValue(
            "paper_size",
            self.paper_size.currentText(),
        )

        self.settings.setValue(
            "logo_path",
            self.logo_path.text().strip(),
        )

        self.settings.setValue(
            "default_payment",
            self.default_payment.currentText(),
        )

        self.settings.setValue(
            "low_stock_limit",
            self.low_stock_limit.value(),
        )

        self.settings.sync()

        self.main_window.update_shop_header(
            self.shop_name.text().strip()
        )

        QMessageBox.information(
            self,
            "Settings Saved",
            "Shop and application settings have been saved successfully.",
        )


class AuthStore:
    """Local single-admin credentials; password is never stored in plaintext."""
    def __init__(self):
        self.path = os.path.join(BASE_DIR, "database", "admin_auth.db")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS credentials (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL)")

    @staticmethod
    def derive(password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 600000).hex()

    def configured(self):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT 1 FROM credentials WHERE id=1").fetchone() is not None

    def username(self):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT username FROM credentials WHERE id=1").fetchone()
        return row[0] if row else ""

    def verify(self, username, password):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT username,salt,password_hash FROM credentials WHERE id=1").fetchone()
        return bool(row and hmac.compare_digest(username, row[0]) and hmac.compare_digest(self.derive(password, row[1]), row[2]))

    def save(self, username, password):
        salt = secrets.token_hex(16)
        hashed = self.derive(password, salt)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO credentials (id,username,salt,password_hash) VALUES (1,?,?,?)", (username, salt, hashed))


class LoginDialog(QDialog):
    def __init__(self, auth, setup=False, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.setup = setup
        self.setWindowTitle("ElectroSmart - " + ("Create Admin Account" if setup else "Admin Login"))
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(13)
        title = QLabel("Create Administrator Account" if setup else "Welcome to ElectroSmart")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #1E293B;")
        layout.addWidget(title)
        subtitle = QLabel("Set up your first admin login." if setup else "Sign in to access your shop management system.")
        subtitle.setStyleSheet("color: #64748B;")
        layout.addWidget(subtitle)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Admin username")
        self.username.setText("admin" if setup else auth.username())
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Username")); layout.addWidget(self.username)
        layout.addWidget(QLabel("Password")); layout.addWidget(self.password)
        self.confirm = None
        if setup:
            self.confirm = QLineEdit()
            self.confirm.setPlaceholderText("Confirm password")
            self.confirm.setEchoMode(QLineEdit.Password)
            layout.addWidget(QLabel("Confirm Password")); layout.addWidget(self.confirm)
        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(lambda checked: self.password.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        layout.addWidget(self.show_password)
        btn = QPushButton("Create Account" if setup else "Login")
        btn.setIcon(qta.icon("fa5s.lock-open", color="white"))
        btn.setStyleSheet("QPushButton {background:#2563EB;color:white;padding:12px;border-radius:7px;font-weight:600;}")
        btn.clicked.connect(self.submit)
        layout.addWidget(btn)
        self.password.returnPressed.connect(self.submit)
        if self.confirm:
            self.confirm.returnPressed.connect(self.submit)

    def submit(self):
        username = self.username.text().strip()
        password = self.password.text()
        if self.setup:
            if not username or len(password) < 8:
                QMessageBox.warning(self, "Invalid Details", "Enter a username and a password of at least 8 characters.")
                return
            if password != self.confirm.text():
                QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                return
            self.auth.save(username, password)
            QSettings(SETTINGS_ORG, SETTINGS_APP).setValue("admin/username", username)
            self.accept()
        elif self.auth.verify(username, password):
            self.accept()
        else:
            self.password.clear()
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")


class AdminPage(QWidget):
    """Admin profile, password change, and logout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.auth = AuthStore()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30,25,30,25)
        layout.setSpacing(14)
        title = QLabel("Administrator & Security")
        title.setStyleSheet("font-size:28px;font-weight:700;color:#1E293B;")
        layout.addWidget(title)
        card = QFrame()
        card.setStyleSheet("QFrame {background:white;border-radius:12px;}")
        form = QFormLayout(card)
        form.setContentsMargins(24,24,24,24)
        self.name = QLineEdit(); self.username = QLineEdit()
        self.email = QLineEdit(); self.phone = QLineEdit()
        for label,field in (("Full name",self.name),("Username",self.username),("Email",self.email),("Phone",self.phone)):
            form.addRow(label+":",field)
        save = QPushButton("Save Profile")
        save.setIcon(qta.icon("fa5s.save",color="#2563EB"))
        save.clicked.connect(self.save_profile)
        form.addRow("",save)
        layout.addWidget(card)
        security = QFrame(); security.setStyleSheet("QFrame {background:white;border-radius:12px;}")
        sf = QFormLayout(security); sf.setContentsMargins(24,20,24,20)
        self.current = QLineEdit(); self.new = QLineEdit(); self.confirm = QLineEdit()
        for field in (self.current,self.new,self.confirm): field.setEchoMode(QLineEdit.Password)
        sf.addRow("Current password:",self.current)
        sf.addRow("New password:",self.new)
        sf.addRow("Confirm new password:",self.confirm)
        change = QPushButton("Change Password")
        change.setIcon(qta.icon("fa5s.key",color="#2563EB"))
        change.clicked.connect(self.change_password)
        sf.addRow("",change)
        layout.addWidget(security)
        logout = QPushButton("Logout")
        logout.setIcon(qta.icon("fa5s.sign-out-alt",color="#DC2626"))
        logout.clicked.connect(lambda: self.window().logout())
        layout.addWidget(logout)
        layout.addStretch()
        self.load_profile()

    def load_profile(self):
        self.name.setText(str(self.settings.value("admin/name","Admin")))
        self.username.setText(self.auth.username())
        self.email.setText(str(self.settings.value("admin/email","")))
        self.phone.setText(str(self.settings.value("admin/phone","")))

    def save_profile(self):
        name = self.name.text().strip()
        username = self.username.text().strip()
        if not name or not username:
            QMessageBox.warning(self,"Required","Name and username are required."); return
        email = self.email.text().strip()
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            QMessageBox.warning(self,"Invalid Email","Please enter a valid email."); return
        old_username = self.auth.username()
        if username != old_username:
            password, ok = QInputDialog.getText(self,"Confirm Username Change","Enter current password:",QLineEdit.Password)
            if not ok: return
            if not self.auth.verify(old_username,password):
                QMessageBox.warning(self,"Denied","Incorrect current password."); return
            self.auth.save(username,password)
        for key,value in (("name",name),("username",username),("email",email),("phone",self.phone.text().strip())):
            self.settings.setValue("admin/"+key,value)
        self.settings.sync()
        self.window().user_button.setText(name)
        QMessageBox.information(self,"Saved","Admin profile updated.")

    def change_password(self):
        if not self.auth.verify(self.auth.username(),self.current.text()):
            QMessageBox.warning(self,"Denied","Current password is incorrect."); return
        if len(self.new.text()) < 8:
            QMessageBox.warning(self,"Weak Password","Use at least 8 characters."); return
        if self.new.text() != self.confirm.text():
            QMessageBox.warning(self,"Mismatch","New passwords do not match."); return
        self.auth.save(self.auth.username(),self.new.text())
        for field in (self.current,self.new,self.confirm): field.clear()
        QMessageBox.information(self,"Updated","Password changed successfully.")

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            SETTINGS_ORG,
            SETTINGS_APP,
        )

        self.setWindowTitle(
            "Nadeem Shahanvi - Electrical Shop Management System"
        )

        self.resize(1300, 750)
        self.setMinimumSize(1100, 650)

        self.apply_global_style()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

      
        sidebar = QFrame()
        sidebar.setFixedWidth(235)
        sidebar.setObjectName("Sidebar")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(7)

        self.logo_label = QLabel()
        self.logo_label.setWordWrap(True)
        self.logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.logo_label.setMinimumHeight(70)
        self.logo_label.setStyleSheet(
            "color: white; font-size: 14px; "
            "font-weight: bold; padding: 6px 4px;"
        )

        self.subtitle_label = QLabel(
            "Electrical Shop System"
        )
        self.subtitle_label.setStyleSheet(
            "color: #94A3B8; font-size: 11px; "
            "padding-left: 10px;"
        )

        sidebar_layout.addWidget(self.logo_label)
        sidebar_layout.addWidget(self.subtitle_label)
        sidebar_layout.addSpacing(20)

        self.buttons = []

        dashboard_btn = self.create_nav_button(
            "Dashboard"
        )
        pos_btn = self.create_nav_button(
            "POS Billing"
        )
        products_btn = self.create_nav_button(
            "Products"
        )
        inventory_btn = self.create_nav_button(
            "Inventory"
        )
        sales_btn = self.create_nav_button(
            "Sales History"
        )
        repair_btn = self.create_nav_button(
            "Repairing & Maintenance"
        )
        reports_btn = self.create_nav_button(
            "Reports"
        )
        settings_btn = self.create_nav_button(
            "Settings"
        )

        dashboard_btn.setIcon(qta.icon("fa5s.home", color="#CBD5E1"))
        pos_btn.setIcon(qta.icon("fa5s.cash-register", color="#CBD5E1"))
        products_btn.setIcon(qta.icon("fa5s.boxes", color="#CBD5E1"))
        inventory_btn.setIcon(qta.icon("fa5s.warehouse", color="#CBD5E1"))
        sales_btn.setIcon(qta.icon("fa5s.receipt", color="#CBD5E1"))
        repair_btn.setIcon(qta.icon("fa5s.tools", color="#CBD5E1"))
        reports_btn.setIcon(qta.icon("fa5s.chart-bar", color="#CBD5E1"))
        settings_btn.setIcon(qta.icon("fa5s.cog", color="#CBD5E1"))

        for btn in [
            dashboard_btn,
            pos_btn,
            products_btn,
            inventory_btn,
            sales_btn,
            repair_btn,
            reports_btn,
            settings_btn,
        ]:
            btn.setIconSize(QSize(18, 18))

        for btn in [
            dashboard_btn,
            pos_btn,
            products_btn,
            inventory_btn,
            sales_btn,
            repair_btn,
            reports_btn,
            settings_btn,
        ]:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.user_button = QPushButton(str(self.settings.value("admin/name", "Admin")))
        self.user_button.setIcon(qta.icon("fa5s.user-shield", color="#CBD5E1"))
        self.user_button.setIconSize(QSize(18, 18))
        self.user_button.setCursor(Qt.PointingHandCursor)
        self.user_button.setToolTip("Open administrator profile")
        self.user_button.setStyleSheet("QPushButton {color: #CBD5E1; background: transparent; text-align: left; padding: 10px; border: none;} QPushButton:hover {background: #334155; color: white;}")
        sidebar_layout.addWidget(self.user_button)
       

        self.pages = QStackedWidget()

        self.dashboard_page = self.create_dashboard()
        self.pos_page = POSPage()
        self.products_page = ProductsPage()
        self.sales_history_page = SalesHistoryPage()
        self.repair_page = RepairingPage()
        self.inventory_page = InventoryPage()
        self.reports_page = ReportsPage()
        self.settings_page = SettingsPage(self)
        self.admin_page = AdminPage(self)

        self.page_indexes = {
            "dashboard": self.pages.addWidget(
                self.dashboard_page
            ),
            "pos": self.pages.addWidget(
                self.pos_page
            ),
            "products": self.pages.addWidget(
                self.products_page
            ),
            "inventory": self.pages.addWidget(
                self.inventory_page
            ),
            "sales": self.pages.addWidget(
                self.sales_history_page
            ),
            "repair": self.pages.addWidget(
                self.repair_page
            ),
            "reports": self.pages.addWidget(
                self.reports_page
            ),
            "settings": self.pages.addWidget(
                self.settings_page
            ),
            "admin": self.pages.addWidget(self.admin_page),
        }

        dashboard_btn.clicked.connect(
            lambda: self.show_page("dashboard")
        )

        pos_btn.clicked.connect(
            lambda: self.show_page("pos")
        )

        products_btn.clicked.connect(
            lambda: self.show_page("products")
        )

        inventory_btn.clicked.connect(
            lambda: self.show_page("inventory")
        )

        sales_btn.clicked.connect(
            lambda: self.show_page("sales")
        )

        repair_btn.clicked.connect(
            lambda: self.show_page("repair")
        )

        reports_btn.clicked.connect(
            lambda: self.show_page("reports")
        )

        settings_btn.clicked.connect(
            lambda: self.show_page("settings")
        )

        self.user_button.clicked.connect(lambda: self.show_page("admin"))

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

        self.update_shop_header(
            self.settings.value(
                "shop_name",
                "Nadeem Shahanvi",
            )
        )

        self.show_page("dashboard")


    def apply_global_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #F1F5F9;
            }

            QFrame#Sidebar {
                background-color: #1E293B;
            }

            QPushButton {
                border-radius: 7px;
                padding: 9px 12px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #E2E8F0;
            }

            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                min-height: 32px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 3px 8px;
                background: white;
            }

            QTableWidget {
                background: white;
                border: none;
                border-radius: 8px;
                gridline-color: #E2E8F0;
            }

            QHeaderView::section {
                background: #E2E8F0;
                color: #1E293B;
                padding: 8px;
                border: none;
                font-weight: bold;
            }

            QGroupBox {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                font-weight: bold;
                color: #1E293B;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
            """
        )


    def create_nav_button(self, text):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(43)

        button.setStyleSheet(
            """
            QPushButton {
                color: #CBD5E1;
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 11px 12px;
                font-size: 14px;
                border-radius: 7px;
            }

            QPushButton:hover {
                background-color: #334155;
                color: white;
            }
            """
        )

        return button

    def logout(self):
        self.hide()
        dialog = LoginDialog(AuthStore(), parent=None)
        if dialog.exec() == QDialog.Accepted:
            self.admin_page.load_profile()
            self.show_page("dashboard")
            self.show()
        else:
            QApplication.instance().quit()

    def show_page(self, name):
        index = self.page_indexes[name]
        self.pages.setCurrentIndex(index)

     
        if name == "dashboard":
            self.refresh_dashboard()

        elif name == "reports":
            self.reports_page.load_report()

        elif name == "inventory":
            self.safe_refresh(self.inventory_page)

        elif name == "sales":
            self.safe_refresh(self.sales_history_page)

        elif name == "repair":
            try:
                self.repair_page.refresh_jobs()
            except Exception:
                pass

    def safe_refresh(self, page):
        for method_name in (
            "refresh_data",
            "load_data",
            "load_sales",
            "refresh",
        ):
            method = getattr(page, method_name, None)

            if callable(method):
                try:
                    method()
                except TypeError:
                    pass
                except Exception:
                    pass

                break



    def create_dashboard(self):
        dashboard = QWidget()

        layout = QVBoxLayout(dashboard)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("Dashboard")
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; "
            "color: #1E293B;"
        )
        layout.addWidget(title)

        self.dashboard_subtitle = QLabel(
            "Business overview and today's performance"
        )
        self.dashboard_subtitle.setStyleSheet(
            "font-size: 14px; color: #64748B;"
        )
        layout.addWidget(self.dashboard_subtitle)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)

        self.dashboard_values = {}

        cards = [
            ("sales", "Today's Sales", "Rs. 0", "fa5s.coins"),
            ("products", "Total Products", "0", "fa5s.boxes"),
            ("low_stock", "Low Stock", "0", "fa5s.exclamation-triangle"),
            ("orders", "Today's Orders", "0", "fa5s.receipt"),
        ]

        for index, (
            key,
            title_text,
            value,
            icon,
        ) in enumerate(cards):

            card = QFrame()
            card.setFixedHeight(130)

            card.setStyleSheet(
                """
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                }
                """
            )

            card_layout = QVBoxLayout(card)

            title_label = QLabel(title_text)
            title_label.setStyleSheet(
                "color: #64748B; font-size: 14px;"
            )

            value_label = QLabel(value)
            value_label.setStyleSheet(
                "color: #1E293B; font-size: 25px; "
                "font-weight: bold;"
            )

            icon_label = QLabel()
            icon_label.setPixmap(qta.icon(icon, color="#2563EB").pixmap(26, 26))
            icon_label.setAlignment(Qt.AlignRight)
            icon_label.setStyleSheet(
                "font-size: 20px;"
            )

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            card_layout.addWidget(icon_label)

            self.dashboard_values[key] = value_label

            cards_layout.addWidget(
                card,
                0,
                index,
            )

        layout.addLayout(cards_layout)

        welcome = QFrame()
        welcome.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
            """
        )

        welcome_layout = QVBoxLayout(welcome)

        self.welcome_title = QLabel()
        self.welcome_title.setStyleSheet(
            "font-size: 22px; font-weight: bold; "
            "color: #1E293B;"
        )

        welcome_text = QLabel(
            "Manage products, stock, sales and billing from one place."
        )
        welcome_text.setStyleSheet(
            "font-size: 14px; color: #64748B;"
        )

        welcome_layout.addWidget(
            self.welcome_title
        )
        welcome_layout.addWidget(
            welcome_text
        )

        layout.addWidget(welcome)

        quick = QFrame()
        quick.setStyleSheet(
            "QFrame { background: white; border-radius: 12px; }"
        )

        quick_layout = QVBoxLayout(quick)

        quick_title = QLabel("Quick Actions")
        quick_title.setStyleSheet(
            "font-size: 17px; font-weight: bold; "
            "color: #1E293B;"
        )

        quick_layout.addWidget(
            quick_title
        )

        quick_row = QHBoxLayout()

        for text, page, icon_name in [
            ("New Sale", "pos", "fa5s.shopping-cart"),
            ("Products", "products", "fa5s.box-open"),
            ("Inventory", "inventory", "fa5s.warehouse"),
            ("Reports", "reports", "fa5s.chart-line"),
        ]:
            btn = QPushButton(text)
            btn.setIcon(qta.icon(icon_name, color="#2563EB"))
            btn.setIconSize(QSize(19, 19))
            btn.setMinimumHeight(42)
            btn.setCursor(Qt.PointingHandCursor)

            btn.clicked.connect(
                lambda checked=False, p=page:
                self.show_page(p)
            )

            quick_row.addWidget(btn)

        quick_layout.addLayout(
            quick_row
        )

        layout.addWidget(quick)

        layout.addStretch()

        return dashboard

    def refresh_dashboard(self):
        conn = None

        try:
            conn = db_connect()

            sales = 0.0
            orders = 0
            products = 0
            low_stock = 0

            if table_exists(conn, "sales"):
                sales_columns = get_table_columns(
                    conn,
                    "sales",
                )

                amount_column = first_existing_column(
                    sales_columns,
                    [
                        "total_amount",
                        "grand_total",
                        "total",
                    ],
                )

                date_column = first_existing_column(
                    sales_columns,
                    [
                        "created_at",
                        "date",
                        "sale_date",
                    ],
                )

                if amount_column and date_column:
                    row = conn.execute(
                        f"""
                        SELECT
                            COALESCE(
                                SUM({amount_column}),
                                0
                            ) AS total,
                            COUNT(*) AS orders
                        FROM sales
                        WHERE date({date_column})
                              = date('now', 'localtime')
                        """
                    ).fetchone()

                    sales = safe_float(
                        row["total"]
                    )

                    orders = int(
                        row["orders"] or 0
                    )

            if table_exists(conn, "products"):
                row = conn.execute(
                    "SELECT COUNT(*) AS total FROM products"
                ).fetchone()

                products = int(
                    row["total"] or 0
                )

                product_columns = get_table_columns(
                    conn,
                    "products",
                )

                stock_column = first_existing_column(
                    product_columns,
                    [
                        "stock",
                        "quantity",
                        "qty",
                    ],
                )

                min_stock_column = first_existing_column(
                    product_columns,
                    [
                        "min_stock",
                        "minimum_stock",
                        "reorder_level",
                    ],
                )

                if stock_column:
                    if min_stock_column:
                        row = conn.execute(
                            f"""
                            SELECT COUNT(*) AS total
                            FROM products
                            WHERE COALESCE({stock_column}, 0)
                                  <= COALESCE(
                                      {min_stock_column},
                                      ?
                                  )
                            """,
                            (
                                safe_float(
                                    self.settings.value(
                                        "low_stock_limit",
                                        5,
                                    ),
                                    5,
                                ),
                            ),
                        ).fetchone()
                    else:
                        row = conn.execute(
                            f"""
                            SELECT COUNT(*) AS total
                            FROM products
                            WHERE COALESCE({stock_column}, 0)
                                  <= ?
                            """,
                            (
                                safe_float(
                                    self.settings.value(
                                        "low_stock_limit",
                                        5,
                                    ),
                                    5,
                                ),
                            ),
                        ).fetchone()

                    low_stock = int(
                        row["total"] or 0
                    )

        except Exception:
            sales = 0.0
            orders = 0
            products = 0
            low_stock = 0

        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

        self.dashboard_values["sales"].setText(
            f"Rs. {sales:,.2f}"
        )

        self.dashboard_values["products"].setText(
            str(products)
        )

        self.dashboard_values["low_stock"].setText(
            str(low_stock)
        )

        self.dashboard_values["orders"].setText(
            str(orders)
        )

    def update_shop_header(self, shop_name):
        self.logo_label.setText(
            f"{shop_name}"
        )

        self.welcome_title.setText(
            f"Welcome to {shop_name}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName("ElectroSmart")
    app.setOrganizationName(SETTINGS_ORG)

    auth = AuthStore()
    login = LoginDialog(auth, setup=not auth.configured())
    if login.exec() != QDialog.Accepted:
        sys.exit(0)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
