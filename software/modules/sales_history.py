import qtawesome as qta
from PySide6.QtCore import QSize

def apply_professional_icon(button, icon_name, color="#FFFFFF", size=16):
    """Attach a crisp scalable icon without changing existing button behavior."""
    try:
        button.setIcon(qta.icon(icon_name, color=color))
        button.setIconSize(QSize(size, size))
    except Exception:
        pass
    return button

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QLineEdit,
    QFileDialog,
    QSizePolicy,
)

import os
import shutil

from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl, Qt

from utils.invoice_generator import generate_invoice
from modules.edit_sale import EditSaleDialog
from database.database_manager import DatabaseManager


class SalesHistoryPage(QWidget):
    """Professional Sales History screen for ElectroSmart."""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_sales()


    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(16)

        header_layout = QHBoxLayout()

        title = QLabel("Sales History")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #1E293B;
            }
        """)

        self.refresh_button = apply_professional_icon(QPushButton('Refresh'), 'fa5s.sync-alt', '#FFFFFF')
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.load_sales)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)
        main_layout.addLayout(header_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search invoice or customer...")
        self.search_input.textChanged.connect(self.search_sales)
        self.search_input.setMinimumHeight(42)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: white;
                padding: 8px 12px;
                font-size: 14px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 1px solid #2563EB; }
        """)
        main_layout.addWidget(self.search_input)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(11)
        self.sales_table.setHorizontalHeaderLabels([
            "ID",
            "Invoice Number",
            "Customer",
            "Subtotal",
            "Labour",
            "Discount",
            "Total Amount",
            "Payment",
            "Date & Time",
            "Details",
            "Actions",
        ])

        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sales_table.setWordWrap(False)
        self.sales_table.verticalHeader().setDefaultSectionSize(38)
        self.sales_table.verticalHeader().setVisible(True)
        self.sales_table.setMinimumHeight(450)
        self.sales_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        header = self.sales_table.horizontalHeader()
        header.setStretchLastSection(False)

        widths = [
            45,   
            95,   
            110,  
            95,   
            90,   
            90,   
            105,  
            85,   
            135,  
            70,   
            220,  
        ]
        for index, width in enumerate(widths):
            header.setSectionResizeMode(index, QHeaderView.Fixed)
            self.sales_table.setColumnWidth(index, width)

        self.sales_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                gridline-color: #E2E8F0;
                font-size: 12px;
                color: #0F172A;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #0F172A;
            }
            QHeaderView::section {
                background-color: #1E293B;
                color: white;
                padding: 9px 5px;
                border: none;
                font-weight: 700;
                font-size: 12px;
            }
        """)

        main_layout.addWidget(self.sales_table)

    @staticmethod
    def _value(row, key, default=0):
        """Safely read a sqlite3.Row/dict value."""
        try:
            value = row[key]
            return default if value is None else value
        except (KeyError, IndexError, TypeError):
            return default

    def _calculate_subtotal(self, sale):
        try:
            items = self.db.get_sale_items(sale["id"])
            return sum(float(item["subtotal"] or 0) for item in items)
        except Exception:
            return 0.0

    @staticmethod
    def _money(value):
        try:
            return f"Rs. {float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "Rs. 0.00"

    def _make_button(self, text, background, hover, slot):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(28)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(slot)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {background};
                color: white;
                border: none;
                padding: 5px 7px;
                border-radius: 5px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """)
        return button


    def load_sales(self):
        try:
            sales = self.db.get_sales()
            self.display_sales(sales)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Sales History Error",
                f"Could not load sales history.\n\n{error}",
            )

    def showEvent(self, event):
        super().showEvent(event)
        self.load_sales()

    def display_sales(self, sales):
        self.sales_table.setRowCount(0)
        self.sales_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            sale_id = self._value(sale, "id", "")
            invoice = str(self._value(sale, "invoice_number", ""))
            customer = str(self._value(sale, "customer_name", "")) or "Walk-in Customer"
            payment = str(self._value(sale, "payment_method", "Cash"))
            created_at = str(self._value(sale, "created_at", ""))

            subtotal = self._calculate_subtotal(sale)
            labour = float(self._value(sale, "labour_amount", 0) or 0)
            discount = float(self._value(sale, "discount", 0) or 0)
            total = float(self._value(sale, "total_amount", 0) or 0)

            values = [
                str(sale_id),
                invoice,
                customer,
                self._money(subtotal),
                self._money(labour),
                self._money(discount),
                self._money(total),
                payment,
                created_at,
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if column in (0, 3, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                self.sales_table.setItem(row, column, item)

            details_button = self._make_button(
                "View",
                "#16A34A",
                "#15803D",
                lambda checked=False, s=sale: self.show_sale_details(s),
            )
            self.sales_table.setCellWidget(row, 9, details_button)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(3, 2, 3, 2)
            action_layout.setSpacing(4)

            edit_button = self._make_button(
                "Edit",
                "#F59E0B",
                "#D97706",
                lambda checked=False, s=sale: self.edit_sale(s),
            )
            open_button = self._make_button(
                "Open PDF",
                "#2563EB",
                "#1D4ED8",
                lambda checked=False, s=sale: self.open_sale_pdf(s),
            )
            export_button = self._make_button(
                "Export",
                "#7C3AED",
                "#6D28D9",
                lambda checked=False, s=sale: self.export_sale_pdf(s),
            )

            action_layout.addWidget(edit_button)
            action_layout.addWidget(open_button)
            action_layout.addWidget(export_button)
            self.sales_table.setCellWidget(row, 10, action_widget)

        self.sales_table.resizeRowsToContents()


    def edit_sale(self, sale):
        try:
            dialog = EditSaleDialog(
                sale_id=sale["id"],
                parent=self,
            )
            if dialog.exec():
                self.load_sales()
        except Exception as error:
            QMessageBox.critical(self, "Edit Sale Error", str(error))


    def generate_sale_pdf(self, sale):
        items = self.db.get_sale_items(sale["id"])

        cart_items = []
        for item in items:
            cart_items.append({
                "product_id": item["product_id"],
                "name": item["product_name"],
                "price": item["price"],
                "quantity": item["quantity"],
            })

        subtotal = sum(
            float(item["price"] or 0) * int(item["quantity"] or 0)
            for item in cart_items
        )

        labour_amount = float(self._value(sale, "labour_amount", 0) or 0)
        discount = float(self._value(sale, "discount", 0) or 0)
        total_amount = float(self._value(sale, "total_amount", 0) or 0)
        cash_received = float(self._value(sale, "cash_received", 0) or 0)
        paper_size = self._value(sale, "paper_size", "A4") or "A4"
        customer_phone = ""

        try:
            full_sale = self.db.get_sale_by_id(sale["id"])
            if full_sale:
                customer_phone = self._value(full_sale, "customer_phone", "") or ""
        except Exception:
            pass

        return generate_invoice(
            invoice_number=self._value(sale, "invoice_number", ""),
            cart_items=cart_items,
            total_amount=total_amount,
            payment_method=self._value(sale, "payment_method", "Cash"),
            customer_name=self._value(sale, "customer_name", ""),
            customer_phone=customer_phone,
            subtotal=subtotal,
            labour_amount=labour_amount,
            discount=discount,
            cash_received=cash_received,
            change=max(0, cash_received - total_amount),
            paper_size=paper_size,
        )

    def open_sale_pdf(self, sale):
        try:
            pdf_path = self.generate_sale_pdf(sale)
            if pdf_path and os.path.exists(pdf_path):
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(os.path.abspath(pdf_path))
                )
            else:
                QMessageBox.warning(
                    self,
                    "PDF Not Found",
                    "Bill PDF could not be generated.",
                )
        except Exception as error:
            QMessageBox.critical(self, "PDF Error", str(error))


    def export_sale_pdf(self, sale):
        try:
            pdf_path = self.generate_sale_pdf(sale)
            if not pdf_path or not os.path.exists(pdf_path):
                QMessageBox.warning(
                    self,
                    "PDF Not Found",
                    "Bill PDF could not be generated.",
                )
                return

            invoice_number = str(
                self._value(sale, "invoice_number", "Invoice")
            ).strip()

            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Invoice PDF",
                f"{invoice_number}.pdf",
                "PDF Files (*.pdf)",
            )

            if not save_path:
                return

            if not save_path.lower().endswith(".pdf"):
                save_path += ".pdf"

            source_path = os.path.abspath(pdf_path)
            destination_path = os.path.abspath(save_path)

            if source_path.lower() != destination_path.lower():
                shutil.copy2(source_path, destination_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Invoice {invoice_number} exported successfully!\n\n"
                f"Saved at:\n{destination_path}",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export PDF Error",
                f"Could not export the invoice PDF.\n\n{error}",
            )


    def search_sales(self):
        text = self.search_input.text().strip().lower()
        sales = self.db.get_sales()

        if not text:
            self.display_sales(sales)
            return

        filtered_sales = []
        for sale in sales:
            invoice = str(self._value(sale, "invoice_number", "")).lower()
            customer = str(self._value(sale, "customer_name", "")).lower()
            if text in invoice or text in customer:
                filtered_sales.append(sale)

        self.display_sales(filtered_sales)

    def show_sale_details(self, sale):
        try:
            items = self.db.get_sale_items(sale["id"])

            invoice = self._value(sale, "invoice_number", "")
            customer = self._value(sale, "customer_name", "") or "Walk-in Customer"
            payment = self._value(sale, "payment_method", "Cash")
            subtotal = sum(float(item["subtotal"] or 0) for item in items)
            labour = float(self._value(sale, "labour_amount", 0) or 0)
            discount = float(self._value(sale, "discount", 0) or 0)
            total = float(self._value(sale, "total_amount", 0) or 0)

            details = (
                f"Invoice: {invoice}\n"
                f"Customer: {customer}\n"
                f"Payment: {payment}\n\n"
                f"PRODUCTS:\n"
            )

            details += "-" * 42 + "\n"

            for item in items:
                details += (
                    f"{item['product_name']}\n"
                    f"Qty: {item['quantity']} × "
                    f"Rs. {float(item['price']):,.2f} = "
                    f"Rs. {float(item['subtotal']):,.2f}\n\n"
                )

            details += "-" * 42 + "\n"
            details += (
                f"Subtotal:       Rs. {subtotal:,.2f}\n"
                f"Labour Charges: Rs. {labour:,.2f}\n"
                f"Discount:       Rs. {discount:,.2f}\n"
                f"TOTAL:          Rs. {total:,.2f}"
            )

            QMessageBox.information(self, "Sale Details", details)

        except Exception as error:
            QMessageBox.critical(self, "Details Error", str(error))
