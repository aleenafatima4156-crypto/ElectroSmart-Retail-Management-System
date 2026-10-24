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
    QGridLayout,
    QLabel,
    QInputDialog,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QFileDialog
)
from PySide6.QtCore import Qt, QUrl
import os
import shutil

from database.database_manager import DatabaseManager
from utils.invoice_generator import generate_invoice
from PySide6.QtGui import QDesktopServices


class POSPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()
        self.cart = []
        self.last_pdf_path = None
        self.last_invoice_number = None
        self.last_total_amount = 0.0
        self.last_labour_amount = 0.0
        self.last_payment_method = ""
        self.last_customer_name = ""
        self.last_customer_phone = ""

        self.setup_ui()
        self.load_products()
        self.open_pdf_button.setEnabled(False)
        self.export_pdf_button.setEnabled(False)

    def open_pdf_bill(self):

        if not self.last_pdf_path:
            QMessageBox.warning(
                self,
                "No Bill",
                "Please complete a sale first."
            )
            return

        if not os.path.exists(self.last_pdf_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                "Invoice PDF file nahi mili."
            )
            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(self.last_pdf_path)
        )

    def export_pdf_bill(self):

        if not self.last_pdf_path:
            QMessageBox.warning(
                self,
                "No Bill",
                "Please complete a sale first."
            )
            return

        if not os.path.exists(self.last_pdf_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                "Invoice PDF file nahi mili."
            )
            return

        invoice_number = self.last_invoice_number or "Invoice"

        default_name = f"{invoice_number}.pdf"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Invoice PDF",
            default_name,
            "PDF Files (*.pdf)"
        )

        if not save_path:
            return

        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        try:
  
            if os.path.abspath(save_path) != os.path.abspath(self.last_pdf_path):
                shutil.copy2(self.last_pdf_path, save_path)

            QMessageBox.information(
                self,
                "PDF Exported",
                f"Invoice PDF exported successfully.\n\n"
                f"Location:\n{save_path}"
            )


            QDesktopServices.openUrl(
                QUrl.fromLocalFile(save_path)
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Could not export invoice PDF.\n\n{error}"
            )
            

    def select_paper_size(self):

        options = [
            "A4",
            "A5",
            "A6",
            "Thermal 80mm",
            "Thermal 58mm"
        ]

        paper_size, ok = QInputDialog.getItem(
            self,
            "Select Invoice Paper Size",
            "Choose paper size:",
            options,
            0,
            False
        )

        if not ok:
            return None

        return paper_size

    def show_customer_balance(self):
        """Refresh customer balance when a customer selector exists."""
        if not hasattr(self, "customer_combo") or not hasattr(self, "outstanding_label"):
            return

        customer_id = self.customer_combo.currentData()

        if customer_id is None:
            self.outstanding_label.setText("Outstanding: Rs. 0.00")
            return

        try:
            balance = float(self.db.get_customer_balance(customer_id) or 0)
            self.outstanding_label.setText(
                f"Outstanding: Rs. {balance:,.2f}"
            )
        except Exception:
            self.outstanding_label.setText("Outstanding: Rs. 0.00")

    def payment_method_changed(self):

        payment_method = self.payment_combo.currentText()

        if payment_method == "Cash":
            self.cash_received_label.setText("Cash Received:")
            self.cash_received_input.setPlaceholderText(
                "Enter received cash"
            )
        else:
            self.cash_received_label.setText("Amount Received:")
            self.cash_received_input.setPlaceholderText(
                "Enter amount received"
            )

        self.cash_received_input.setEnabled(True)
        self.cash_received_input.setVisible(True)
        self.cash_received_label.setVisible(True)

        self.update_payment_summary()

    def update_payment_summary(self):

        try:
            received = float(
                self.cash_received_input.text() or 0
            )
        except (ValueError, TypeError):
            received = 0

        try:
            subtotal = sum(
                item["price"] * item["quantity"]
                for item in self.cart
            )

            labour = max(
                0,
                float(self.labour_input.text() or 0)
            )

            discount = max(
                0,
                float(self.discount_input.text() or 0)
            )

            discount = min(
                discount,
                subtotal + labour
            )

            grand_total = (
                subtotal
                + labour
                - discount
            )

            difference = received - grand_total

            if difference >= 0:
                self.change_label.setText(
                    f"Change: Rs. {difference:,.2f}"
                )
            else:
                self.change_label.setText(
                    f"Remaining: Rs. {abs(difference):,.2f}"
                )

        except Exception:
            self.change_label.setText(
                "Change: Rs. 0.00"
            )

    def setup_ui(self):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        main_layout.setSpacing(16)

   
        left_frame = QFrame()

        left_layout = QVBoxLayout(
            left_frame
        )

        title = QLabel("POS Billing")

        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1E293B;
        """)

        left_layout.addWidget(title)

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search product, category, brand or ID..."
        )

        self.search_input.setClearButtonEnabled(True)

        self.search_input.textChanged.connect(
            self.search_products
        )

        self.search_input.setStyleSheet("""
            padding: 10px;
            font-size: 14px;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
        """)

        left_layout.addWidget(
            self.search_input
        )

    
        self.products_table = QTableWidget()

        self.products_table.setColumnCount(5)

        self.products_table.setHorizontalHeaderLabels([
            "Product",
            "Category",
            "Price",
            "Stock",
            "Add"
        ])

        self.products_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.products_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #E2E8F0;
                font-size: 13px;
            }

            QHeaderView::section {
                background: #1E293B;
                color: white;
                padding: 9px;
                border: none;
                font-weight: bold;
            }
        """)

        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.products_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        left_layout.addWidget(
            self.products_table
        )

        right_frame = QFrame()

        right_frame.setFixedWidth(500)

        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)

        right_layout = QVBoxLayout(
            right_frame
        )

        cart_title = QLabel(
            "Current Bill"
        )

        cart_title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #1E293B;
            padding: 5px;
        """)

        right_layout.addWidget(
            cart_title
        )


        self.invoice_label = QLabel()

        self.invoice_label.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
        """)

        right_layout.addWidget(
            self.invoice_label
        )

        self.cart_table = QTableWidget()

        self.cart_table.setColumnCount(5)

        self.cart_table.setHorizontalHeaderLabels([
            "Product",
            "Qty",
            "Price(Edit)",
            "Total",
            "Remove"
        ])

        self.cart_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.cart_table.verticalHeader().setDefaultSectionSize(34)

        self.cart_table.setMinimumHeight(180)

        self.cart_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.cart_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.cart_table.setAlternatingRowColors(True)

        self.cart_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.cart_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                font-size: 12px;
            }

            QHeaderView::section {
                background: #334155;
                color: white;
                padding: 8px;
                border: none;
            }
        """)

        right_layout.addWidget(
            self.cart_table
        )

 
        details_layout = QGridLayout()

        details_layout.setHorizontalSpacing(12)
        details_layout.setVerticalSpacing(5)
        details_layout.setContentsMargins(
            0,
            2,
            0,
            2
        )



        self.subtotal_label = QLabel(
            "Subtotal: Rs. 0.00"
        )

        self.subtotal_label.setStyleSheet("""
            font-size: 15px;
            color: #475569;
            padding: 3px;
        """)

        details_layout.addWidget(
            self.subtotal_label,
            0,
            0
        )


        labour_label = QLabel(
            "Labour Charges:"
        )

        self.labour_input = QLineEdit()

        self.labour_input.setPlaceholderText(
            "Enter labour charges"
        )

        self.labour_input.setText("0")

        self.labour_input.textChanged.connect(
            self.update_cart
        )

        labour_box = QHBoxLayout()

        labour_box.setSpacing(6)

        labour_box.addWidget(
            labour_label
        )

        labour_box.addWidget(
            self.labour_input
        )

        details_layout.addLayout(
            labour_box,
            0,
            1
        )

        discount_label = QLabel(
            "Discount:"
        )

        self.discount_input = QLineEdit()

        self.discount_input.setPlaceholderText(
            "Enter discount"
        )

        self.discount_input.setText("0")

        self.discount_input.textChanged.connect(
            self.update_cart
        )

        discount_box = QHBoxLayout()

        discount_box.setSpacing(6)

        discount_box.addWidget(
            discount_label
        )

        discount_box.addWidget(
            self.discount_input
        )

        details_layout.addLayout(
            discount_box,
            1,
            1
        )

        self.total_label = QLabel(
            "Grand Total: Rs. 0.00"
        )

        self.total_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #16A34A;
            padding: 4px;
        """)

        details_layout.addWidget(
            self.total_label,
            2,
            0,
            1,
            2
        )

    
        payment_label = QLabel(
            "Payment Method"
        )

        self.payment_combo = QComboBox()

        self.payment_combo.addItems([
            "Cash",
            "Card",
            "Easypaisa",
            "JazzCash",
            "Bank Transfer",
            "Credit"
        ])

        self.payment_combo.currentIndexChanged.connect(
            self.payment_method_changed
        )

        payment_box = QHBoxLayout()

        payment_box.setSpacing(6)

        payment_box.addWidget(
            payment_label
        )

        payment_box.addWidget(
            self.payment_combo
        )

        details_layout.addLayout(
            payment_box,
            3,
            0
        )

        self.cash_received_label = QLabel(
            "Cash Received:"
        )

        self.cash_received_input = QLineEdit()

        self.cash_received_input.setPlaceholderText(
            "Enter received cash"
        )

        self.cash_received_input.setText("0")

        self.cash_received_input.textChanged.connect(
            self.update_payment_summary
        )

        cash_box = QHBoxLayout()

        cash_box.setSpacing(6)

        cash_box.addWidget(
            self.cash_received_label
        )

        cash_box.addWidget(
            self.cash_received_input
        )

        details_layout.addLayout(
            cash_box,
            3,
            1
        )

        customer_name_label = QLabel(
            "Customer Name"
        )

        self.customer_name_input = QLineEdit()

        self.customer_name_input.setPlaceholderText(
            "Enter customer name"
        )

        self.customer_name_input.setText(
            "Walk-in Customer"
        )

        name_box = QHBoxLayout()

        name_box.setSpacing(6)

        name_box.addWidget(
            customer_name_label
        )

        name_box.addWidget(
            self.customer_name_input
        )

        details_layout.addLayout(
            name_box,
            4,
            0
        )

        customer_phone_label = QLabel(
            "Customer Phone"
        )

        self.customer_phone_input = QLineEdit()

        self.customer_phone_input.setPlaceholderText(
            "Enter phone number"
        )

        phone_box = QHBoxLayout()

        phone_box.setSpacing(6)

        phone_box.addWidget(
            customer_phone_label
        )

        phone_box.addWidget(
            self.customer_phone_input
        )

        details_layout.addLayout(
            phone_box,
            4,
            1
        )

        self.change_label = QLabel(
            "Change: Rs. 0.00"
        )

        self.change_label.setStyleSheet("""
            color: #16A34A;
            font-size: 13px;
            font-weight: bold;
            padding: 3px;
        """)

        details_layout.addWidget(
            self.change_label,
            5,
            0,
            1,
            2
        )

        right_layout.addLayout(
            details_layout
        )

        self.complete_button = apply_professional_icon(QPushButton('Complete Sale & Generate Bill'), 'fa5s.check-circle', '#FFFFFF')

        self.complete_button.clicked.connect(
            self.complete_sale
        )

        self.complete_button.setStyleSheet("""
            QPushButton {
                background-color: #16A34A;
                color: white;
                border: none;
                padding: 11px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #15803D;
            }
        """)

        right_layout.addWidget(
            self.complete_button
        )

        bill_buttons_layout = QHBoxLayout()
elf.open_pdf_button = apply_professional_icon(QPushButton('Open PDF'), 'fa5s.file-pdf', '#FFFFFF')

        self.open_pdf_button.setEnabled(False)

        self.open_pdf_button.clicked.connect(
            self.open_pdf_bill
        )

        self.open_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #334155;
            }

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }
        """)

        self.export_pdf_button = apply_professional_icon(QPushButton('Export PDF'), 'fa5s.file-pdf', '#FFFFFF')

        self.export_pdf_button.setEnabled(False)

        self.export_pdf_button.clicked.connect(
            self.export_pdf_bill
        )

        self.export_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #6D28D9;
            }

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }
        """)

        self.new_bill_button = apply_professional_icon(QPushButton('New Bill'), 'fa5s.file-invoice', '#FFFFFF')

        self.new_bill_button.clicked.connect(
            self.start_new_bill
        )

        self.new_bill_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 8px;.
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            } 

            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)

        bill_buttons_layout.addWidget(
            self.open_pdf_button
        )

        bill_buttons_layout.addWidget(
            self.export_pdf_button
        )

        bill_buttons_layout.addWidget(
            self.new_bill_button
        )

        right_layout.addLayout(
            bill_buttons_layout
        )

        main_layout.addWidget(
            left_frame,
            3
        )

        main_layout.addWidget(
            right_frame,
            2
        )

        self.payment_method_changed()

    def start_new_bill(self):

        if self.cart:
            reply = QMessageBox.question(
                self,
                "Start New Bill",
                "Current bill has items. Discard it and start a new bill?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

        self.cart.clear()

        self.labour_input.setText("0")
        self.discount_input.setText("0")
        self.cash_received_input.setText("0")

        self.customer_name_input.setText(
            "Walk-in Customer"
        )

        self.customer_phone_input.clear()

        self.update_cart()
        self.load_products()

        self.last_pdf_path = None
        self.last_invoice_number = None
        self.last_total_amount = 0.0
        self.last_labour_amount = 0.0
        self.last_payment_method = ""
        self.last_customer_name = ""
        self.last_customer_phone = ""

        self.open_pdf_button.setEnabled(False)
        self.export_pdf_button.setEnabled(False)

    def load_products(self):

        products = self.db.get_products()

        self.display_products(products)

        try:
            invoice_number = self.db.get_next_invoice_number()
        except Exception:
            invoice_number = "Pending"

        self.invoice_label.setText(
            f"Invoice: {invoice_number}"
        )

    def display_products(self, products):

        self.products_table.setRowCount(
            len(products)
        )

        for row, product in enumerate(products):

            self.products_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(product["name"])
                )
            )

            self.products_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(product["category"] or "")
                )
            )

            self.products_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    f"Rs. {float(product['selling_price']):,.2f}"
                )
            )

            stock_item = QTableWidgetItem(
                str(product["stock"])
            )

            stock_item.setTextAlignment(
                Qt.AlignCenter
            )

            self.products_table.setItem(
                row,
                3,
                stock_item
            )

            add_button = apply_professional_icon(QPushButton('Add'), 'fa5s.plus', '#FFFFFF')

            add_button.clicked.connect(
                lambda checked=False,
                p=product:
                self.add_to_cart(p)
            )

            add_button.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    color: white;
                    border: none;
                    padding: 6px;
                    border-radius: 5px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #1D4ED8;
                }
            """)

            self.products_table.setCellWidget(
                row,
                4,
                add_button
            )

    def search_products(self):

        text = (
            self.search_input
            .text()
            .lower()
            .strip()
        )

        products = self.db.get_products()

        filtered_products = []

        for product in products:

            product_name = str(
                product["name"] or ""
            ).lower()

            category = str(
                product["category"] or ""
            ).lower()

            brand = str(
                product["brand"] or ""
            ).lower()

            product_id = str(
                product["id"] or ""
            ).lower()

            if (
                not text
                or text in product_name
                or text in category
                or text in brand
                or text in product_id
            ):
                filtered_products.append(
                    product
                )

        self.display_products(
            filtered_products
        )

    def add_to_cart(self, product):

        if int(product["stock"] or 0) <= 0:

            QMessageBox.warning(
                self,
                "Out of Stock",
                f"{product['name']} is out of stock."
            )

            return

        for item in self.cart:

            if item["product_id"] == product["id"]:

                if item["quantity"] < item["max_stock"]:
                    item["quantity"] += 1
                else:
                    QMessageBox.warning(
                        self,
                        "Stock Limit",
                        f"Only {item['max_stock']} available."
                    )

                self.update_cart()
                return

        self.cart.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": float(
                product["selling_price"]
            ),
            "quantity": 1,
            "max_stock": int(
                product["stock"]
            )
        })

        self.update_cart()

    def change_price(self, row, price):

        if row < 0 or row >= len(self.cart):
            return

        try:
            price = float(price)
        except (ValueError, TypeError):
            return

        if price != price or price in (
            float("inf"),
            float("-inf")
        ):
            return

        if price < 0:
            price = 0

        self.cart[row]["price"] = price

        quantity = self.cart[row]["quantity"]

        row_total = price * quantity

        self.cart_table.setItem(
            row,
            3,
            QTableWidgetItem(
                f"Rs. {row_total:,.2f}"
            )
        )

        self.update_totals()


    def update_cart(self):

        self.cart_table.setRowCount(
            len(self.cart)
        )

        for row, item in enumerate(self.cart):

            # PRODUCT NAME

            self.cart_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    item["name"]
                )
            )

            # 

            quantity_spinbox = QSpinBox()

            quantity_spinbox.setMinimum(1)

            quantity_spinbox.setMaximum(
                item["max_stock"]
            )

            quantity_spinbox.setValue(
                item["quantity"]
            )

            quantity_spinbox.valueChanged.connect(
                lambda value,
                current_row=row:
                self.change_quantity(
                    current_row,
                    value
                )
            )

            self.cart_table.setCellWidget(
                row,
                1,
                quantity_spinbox
            )

            price_spinbox = QDoubleSpinBox()

            price_spinbox.setMinimum(0)

            price_spinbox.setMaximum(
                100000000
            )

            price_spinbox.setDecimals(2)

            price_spinbox.setSingleStep(10)

            price_spinbox.setPrefix(
                "Rs. "
            )

            price_spinbox.blockSignals(True)

            price_spinbox.setValue(
                float(item["price"])
            )

            price_spinbox.blockSignals(False)

            price_spinbox.valueChanged.connect(
                lambda value,
                current_row=row:
                self.change_price(
                    current_row,
                    value
                )
            )

            self.cart_table.setCellWidget(
                row,
                2,
                price_spinbox
            )


            item_total = (
                item["price"]
                * item["quantity"]
            )

            self.cart_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    f"Rs. {item_total:,.2f}"
                )
            )

            remove_button = apply_professional_icon(QPushButton('Remove'), 'fa5s.trash-alt', '#FFFFFF')

            remove_button.clicked.connect(
                lambda checked=False,
                current_row=row:
                self.remove_item(
                    current_row
                )
            )

            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px;
                }

                QPushButton:hover {
                    background-color: #B91C1C;
                }
            """)

            self.cart_table.setCellWidget(
                row,
                4,
                remove_button
            )

        self.update_totals()

    def update_totals(self):

        subtotal = sum(
            item["price"] * item["quantity"]
            for item in self.cart
        )

        try:
            labour_amount = float(
                self.labour_input.text() or 0
            )
        except (ValueError, TypeError):
            labour_amount = 0

        if labour_amount < 0:
            labour_amount = 0

   

        try:
            discount = float(
                self.discount_input.text() or 0
            )
        except (ValueError, TypeError):
            discount = 0

        if discount < 0:
            discount = 0

        discount = min(
            discount,
            subtotal + labour_amount
        )

        grand_total = (
            subtotal
            + labour_amount
            - discount
        )

        self.subtotal_label.setText(
            f"Subtotal: Rs. {subtotal:,.2f}"
        )

        self.total_label.setText(
            f"Grand Total: Rs. {grand_total:,.2f}"
        )

        self.update_payment_summary()

    def change_quantity(self, row, quantity):

        if row < len(self.cart):

            max_stock = int(
                self.cart[row].get(
                    "max_stock",
                    0
                )
            )

            quantity = max(
                1,
                min(
                    int(quantity),
                    max_stock
                )
            )

            self.cart[row]["quantity"] = quantity

            price = self.cart[row]["price"]

            row_total = price * quantity

            self.cart_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    f"Rs. {row_total:,.2f}"
                )
            )

            self.update_totals()

    def remove_item(self, row):

        if row < len(self.cart):

            self.cart.pop(row)

            self.update_cart()


    def complete_sale(self):

        # CHECK CART

        if not self.cart:

            QMessageBox.warning(
                self,
                "Empty Cart",
                "Please add products first."
            )

            return

        subtotal = sum(
            item["price"] * item["quantity"]
            for item in self.cart
        )

        try:
            labour_amount = float(
                self.labour_input.text() or 0
            )
        except (ValueError, TypeError):

            QMessageBox.warning(
                self,
                "Invalid Labour Charges",
                "Please enter a valid labour amount."
            )

            return

        if (
            labour_amount != labour_amount
            or labour_amount in (
                float("inf"),
                float("-inf")
            )
            or labour_amount < 0
        ):

            QMessageBox.warning(
                self,
                "Invalid Labour Charges",
                "Labour charges must be a valid non-negative amount."
            )

            return

        try:
            discount = float(
                self.discount_input.text() or 0
            )
        except (ValueError, TypeError):

            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Please enter a valid discount amount."
            )

            return

        if (
            discount != discount
            or discount in (
                float("inf"),
                float("-inf")
            )
        ):

            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Discount must be a normal numeric amount."
            )

            return

        if discount < 0:

            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Discount cannot be negative."
            )

            return

        if discount > (
            subtotal + labour_amount
        ):

            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Discount cannot be greater than subtotal + labour charges."
            )

            return

       
        customer_name = (
            self.customer_name_input
            .text()
            .strip()
        )

        phone = (
            self.customer_phone_input
            .text()
            .strip()
        )

        customer_id = None

        if not customer_name:
            customer_name = "Walk-in Customer"

        grand_total = (
            subtotal
            + labour_amount
            - discount
        )

        payment_method = (
            self.payment_combo.currentText()
        )

        try:
            cash_received = float(
                self.cash_received_input.text() or 0
            )
        except (ValueError, TypeError):

            QMessageBox.warning(
                self,
                "Invalid Amount",
                "Please enter a valid received amount."
            )

            return

        if (
            cash_received != cash_received
            or cash_received in (
                float("inf"),
                float("-inf")
            )
            or cash_received < 0
        ):

            QMessageBox.warning(
                self,
                "Invalid Amount",
                "Amount received must be a valid non-negative amount."
            )

            return

    
        if (
            payment_method == "Cash"
            and cash_received < grand_total
        ):

            QMessageBox.warning(
                self,
                "Insufficient Cash",
                f"Required amount: Rs. {grand_total:,.2f}\n"
                f"Received amount: Rs. {cash_received:,.2f}"
            )

            return

   
        change = cash_received - grand_total

       
        if payment_method == "Credit":

            if (
                not customer_name
                or customer_name == "Walk-in Customer"
            ):

                QMessageBox.warning(
                    self,
                    "Customer Required",
                    "Please enter customer name for Credit payment."
                )

                return

        paper_size = self.select_paper_size()

        if paper_size is None:
            return

        invoice_number = (
            self.db.get_next_invoice_number()
        )

        try:

           
            self.db.create_sale(
                invoice_number=invoice_number,
                cart_items=self.cart,
                total_amount=grand_total,
                payment_method=payment_method,
                customer_name=customer_name,
                customer_phone=phone,
                customer_id=customer_id,
                discount=discount,
                cash_received=cash_received,
                labour_amount=labour_amount
            )

            pdf_path = generate_invoice(
                invoice_number=invoice_number,
                cart_items=self.cart,
                total_amount=grand_total,
                payment_method=payment_method,
                customer_name=customer_name,
                customer_phone=phone,
                subtotal=subtotal,
                labour_amount=labour_amount,
                discount=discount,
                cash_received=cash_received,
                change=change,
                paper_size=paper_size
            )

            self.last_pdf_path = pdf_path
            self.last_invoice_number = invoice_number
            self.last_total_amount = grand_total
            self.last_labour_amount = labour_amount
            self.last_payment_method = payment_method
            self.last_customer_name = customer_name
            self.last_customer_phone = phone

            self.open_pdf_button.setEnabled(True)
            self.export_pdf_button.setEnabled(True)

            QMessageBox.information(
                self,
                "Sale Completed",
                f"Sale completed successfully!\n\n"
                f"Invoice: {invoice_number}\n"
                f"Subtotal: Rs. {subtotal:,.2f}\n"
                f"Labour Charges: Rs. {labour_amount:,.2f}\n"
                f"Discount: Rs. {discount:,.2f}\n"
                f"Grand Total: Rs. {grand_total:,.2f}\n"
                f"Payment: {payment_method}\n"
                f"Change: Rs. {change:,.2f}\n\n"
                f"Bill generated successfully."
            )

            self.cart = []

            self.labour_input.setText("0")
            self.discount_input.setText("0")
            self.cash_received_input.setText("0")

            self.customer_name_input.setText("")
            self.customer_phone_input.clear()

            self.update_cart()

       
            self.load_products()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Sale Error",
                str(error)
            )
