import os

from utils.invoice_generator import generate_invoice
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QCompleter

)

from PySide6.QtCore import Qt

from database.database_manager import DatabaseManager


class EditSaleDialog(QDialog):

    def __init__(self, sale_id, parent=None):

        super().__init__(parent)

        self.sale_id = sale_id
        self.db = DatabaseManager()

        self.sale = None

        self.setWindowTitle("Edit Bill")
        self.resize(950, 650)

        self.setup_ui()
        self.load_products()
        self.load_sale()


    def setup_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)


        
        title = QLabel("Edit Existing Bill")

        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)

        layout.addWidget(title)

        self.invoice_label = QLabel("Invoice: ")

        self.invoice_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
        """)

        layout.addWidget(self.invoice_label)

        customer_name_layout = QHBoxLayout()

        customer_name_layout.addWidget(
            QLabel("Customer Name:")
        )

        self.customer_name_input = QLineEdit()

        self.customer_name_input.setPlaceholderText(
            "Enter customer name"
        )

        customer_name_layout.addWidget(
            self.customer_name_input
        )

        layout.addLayout(
            customer_name_layout
        )


        customer_phone_layout = QHBoxLayout()

        customer_phone_layout.addWidget(
            QLabel("Customer Phone:")
        )

        self.customer_phone_input = QLineEdit()

        self.customer_phone_input.setPlaceholderText(
            "Enter phone number"
        )

        customer_phone_layout.addWidget(
            self.customer_phone_input
        )

        layout.addLayout(
            customer_phone_layout
        )

        product_layout = QHBoxLayout()

        product_layout.addWidget(
            QLabel("Product:")
        )

        self.product_combo = QComboBox()

        self.product_combo.setMinimumWidth(350)

        self.product_combo.setEditable(True)

        self.product_combo.setInsertPolicy(
            QComboBox.NoInsert
        )

        self.product_combo.setPlaceholderText(
            "Search product..."
        )

        self.product_combo.lineEdit().setPlaceholderText(
            "Search product..."
        )

        product_layout.addWidget(
            self.product_combo
        )

        self.add_product_button = QPushButton(
            "Add Product"
        )

        self.add_product_button.clicked.connect(
            self.add_product
        )

        product_layout.addWidget(
            self.add_product_button
        )

        layout.addLayout(product_layout)

        self.sales_table = QTableWidget()

        self.sales_table.setColumnCount(6)

        self.sales_table.setHorizontalHeaderLabels([
            "Product",
            "Quantity",
            "Price (✎ edit)",
            "Subtotal",
            "Remove",
            "Product ID"
        ])

    
        self.sales_table.itemChanged.connect(
            self.price_changed
        )
        self.sales_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.sales_table.setColumnHidden(5, True)
        self.sales_table.itemChanged.connect(self.price_changed)

        layout.addWidget(
            self.sales_table
        )

        discount_layout = QHBoxLayout()

        discount_layout.addWidget(
            QLabel("Discount:")
        )

        self.discount_spin = QDoubleSpinBox()

        self.discount_spin.setMinimum(0)
        self.discount_spin.setMaximum(100000000)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setPrefix("Rs. ")

        self.discount_spin.valueChanged.connect(
            self.update_balance
        )

        discount_layout.addWidget(
            self.discount_spin
        )

        discount_layout.addStretch()

        layout.addLayout(
            discount_layout
        )

     
        labour_layout = QHBoxLayout()

        labour_layout.addWidget(
            QLabel("Labour Charges:")
        )

        self.labour_spin = QDoubleSpinBox()
        self.labour_spin.setMinimum(0)
        self.labour_spin.setMaximum(100000000)
        self.labour_spin.setDecimals(2)
        self.labour_spin.setPrefix("Rs. ")

        self.labour_spin.valueChanged.connect(
            self.update_balance
        )

        labour_layout.addWidget(
            self.labour_spin
        )

        labour_layout.addStretch()

        layout.addLayout(
            labour_layout
        )


       
        payment_layout = QHBoxLayout()

        payment_layout.addWidget(
            QLabel("Payment:")
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

        self.payment_combo.currentTextChanged.connect(
            self.payment_method_changed
        )

        payment_layout.addWidget(
            self.payment_combo
        )

        payment_layout.addWidget(
            QLabel("Cash Received:")
        )

        self.cash_received_spin = QDoubleSpinBox()

        self.cash_received_spin.setMinimum(0)
        self.cash_received_spin.setMaximum(100000000)
        self.cash_received_spin.setDecimals(2)
        self.cash_received_spin.setPrefix("Rs. ")

        self.cash_received_spin.valueChanged.connect(
            self.update_balance
        )

        payment_layout.addWidget(
            self.cash_received_spin
        )

        layout.addLayout(
            payment_layout
        )

    

        self.subtotal_label = QLabel(
            "Subtotal: Rs. 0.00"
        )

        self.labour_label = QLabel(
            "Labour Charges: Rs. 0.00"
        )

        self.discount_label = QLabel(
            "Discount: Rs. 0.00"
        )

        self.total_label = QLabel(
            "Total: Rs. 0.00"
        )

        self.balance_label = QLabel(
            "Balance: Rs. 0.00"
        )

        self.change_label = QLabel(
            "Change: Rs. 0.00"
        )

        self.subtotal_label.setStyleSheet(
            "font-size: 14px;"
        )

        self.labour_label.setStyleSheet(
            "font-size: 14px;"
        )

        self.discount_label.setStyleSheet(
            "font-size: 14px;"
        )

        self.total_label.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        self.balance_label.setStyleSheet(
            "font-size: 14px;"
        )

        self.change_label.setStyleSheet(
            "font-size: 14px;"
        )

        layout.addWidget(
            self.subtotal_label
        )

        layout.addWidget(
            self.labour_label
        )

        layout.addWidget(
            self.discount_label
        )

        layout.addWidget(
            self.total_label
        )

        layout.addWidget(
            self.balance_label
        )

        layout.addWidget(
            self.change_label
        )

    
        buttons_layout = QHBoxLayout()

        buttons_layout.addStretch()

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.clicked.connect(
            self.reject
        )

        buttons_layout.addWidget(
            cancel_button
        )

        save_button = QPushButton(
            "Save Changes"
        )

        save_button.setMinimumWidth(150)

        save_button.clicked.connect(
            self.save_changes
        )

        buttons_layout.addWidget(
            save_button
        )

        layout.addLayout(
            buttons_layout
        )
   

    def load_products(self):

        self.product_combo.clear()

        try:

            products = self.db.get_products()

            for product in products:

                stock = int(
                    product["stock"] or 0
                )

                self.product_combo.addItem(
                    f"{product['name']} | Stock: {stock}",
                    product["id"]
                )
            completer = QCompleter(
                self.product_combo.model(),
                self
            )

            completer.setCaseSensitivity(
                Qt.CaseInsensitive
            )

            completer.setFilterMode(
                Qt.MatchContains
            )

            completer.setCompletionMode(
                QCompleter.PopupCompletion
            )

            self.product_combo.setCompleter(
                completer
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Product Error",
                str(error)
            )

    def load_sale(self):

        try:

            sale = self.db.get_sale_by_id(
                self.sale_id
            )

            items = self.db.get_sale_items(
                self.sale_id
            )

            if not sale:

                QMessageBox.warning(
                    self,
                    "Sale Not Found",
                    "The selected sale could not be found."
                )

                self.reject()
                return

            self.sale = sale

          
            self.invoice_label.setText(
                f"Invoice: {sale['invoice_number']}"
            )

            self.customer_name_input.setText(
            sale["customer_name"] or ""
        )

            self.customer_phone_input.setText(
                sale["customer_phone"] or ""
            )

 

            self.discount_spin.setValue(
                float(sale["discount"] or 0)
                )

            self.labour_spin.setValue(
                float(sale["labour_amount"] or 0)
            )


            self.payment_combo.setCurrentText(
                sale["payment_method"] or "Cash"
            )

            self.cash_received_spin.setValue(
                float(sale["cash_received"] or 0)
            )

        
          
            self.sales_table.setRowCount(0)

            for item in items:

                self.add_existing_item(
                    item
                )

            self.update_balance()

            self.payment_method_changed(
                sale["payment_method"] or "Cash"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Load Error",
                str(error)
            )

            self.reject()



    def add_existing_item(self, item):

        row = self.sales_table.rowCount()

        self.sales_table.insertRow(
            row
        )

  
        self.sales_table.setItem(
            row,
            0,
            QTableWidgetItem(
                item["product_name"]
            )
        )
 
        quantity_spin = QSpinBox()

        quantity_spin.setMinimum(1)
        quantity_spin.setMaximum(100000)

        quantity_spin.setValue(
            int(item["quantity"])
        )

        quantity_spin.valueChanged.connect(
            self.update_balance
        )

        self.sales_table.setCellWidget(
            row,
            1,
            quantity_spin
        )

        price_item = QTableWidgetItem(
            f"{float(item['price']):.2f}"
        )

        price_item.setTextAlignment(
            Qt.AlignCenter
        )

        price_item.setFlags(
            price_item.flags() | Qt.ItemIsEditable
        )

        self.sales_table.setItem(
            row,
            2,
            price_item
        )

        subtotal = (
            float(item["price"])
            *
            int(item["quantity"])
        )

        self.sales_table.setItem(
            row,
            3,
            QTableWidgetItem(
                f"{subtotal:.2f}"
            )
        )

        remove_button = QPushButton(
            "Remove"
        )

        remove_button.clicked.connect(
            self.remove_current_row
        )

        self.sales_table.setCellWidget(
            row,
            4,
            remove_button
        )

        self.sales_table.setItem(
            row,
            5,
            QTableWidgetItem(
                str(item["product_id"])
            )
        )


    def add_product(self):

        product_id = self.product_combo.currentData()

        if product_id is None:

            QMessageBox.warning(
                self,
                "Select Product",
                "Please select a product first."
            )

            return

        try:

            product = self.db.get_product(
                product_id
            )

            if not product:

                QMessageBox.warning(
                    self,
                    "Product Not Found",
                    "Selected product was not found."
                )

                return

        
            for row in range(
                self.sales_table.rowCount()
            ):

                existing_id = (
                    self.sales_table.item(row, 5)
                )

                if (
                    existing_id
                    and
                    int(existing_id.text())
                    ==
                    int(product_id)
                ):

                    quantity_spin = (
                        self.sales_table.cellWidget(
                            row,
                            1
                        )
                    )

                    quantity_spin.setValue(
                        quantity_spin.value() + 1
                    )

                    self.update_balance()

                    return


            if int(product["stock"] or 0) < 1:

                QMessageBox.warning(
                    self,
                    "Out of Stock",
                    f"{product['name']} is currently out of stock."
                )

                return

        
            row = self.sales_table.rowCount()

            self.sales_table.insertRow(
                row
            )

            self.sales_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    product["name"]
                )
            )

            quantity_spin = QSpinBox()

            quantity_spin.setMinimum(1)

            quantity_spin.setMaximum(
                max(
                    1,
                    int(product["stock"])
                )
            )

            quantity_spin.setValue(1)

            quantity_spin.valueChanged.connect(
                self.update_balance
            )

            self.sales_table.setCellWidget(
                row,
                1,
                quantity_spin
            )

            price = float(
                product["selling_price"]
            )

            price_item = QTableWidgetItem(
                f"{price:.2f}"
            )

            price_item.setTextAlignment(
                Qt.AlignCenter
            )

            price_item.setFlags(
                price_item.flags() | Qt.ItemIsEditable
            )

            self.sales_table.setItem(
                row,
                2,
                price_item
            )

            self.sales_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    f"{price:.2f}"
                )
            )

            remove_button = QPushButton(
                "Remove"
            )

            remove_button.clicked.connect(
                self.remove_current_row
            )

            self.sales_table.setCellWidget(
                row,
                4,
                remove_button
            )

            self.sales_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    str(product["id"])
                )
            )

            self.update_balance()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Add Product Error",
                str(error)
            )

    def remove_current_row(self):

        button = self.sender()

        if not button:
            return

        for row in range(
            self.sales_table.rowCount()
        ):

            widget = self.sales_table.cellWidget(
                row,
                4
            )

            if widget is button:

                self.sales_table.removeRow(
                    row
                )

                self.update_balance()

                return

    def price_changed(self, item):
        if item.column() != 2:
            return

        try:
            price = float(item.text().strip())

            if price < 0:
                raise ValueError

        except ValueError:
            self.sales_table.blockSignals(True)
            item.setText("0.00")
            self.sales_table.blockSignals(False)

            QMessageBox.warning(
                self,
                "Invalid Price",
                "Please enter a valid price."
            )

            self.update_balance()
            return

        self.sales_table.blockSignals(True)
        item.setText(f"{price:.2f}")
        self.sales_table.blockSignals(False)

        self.update_balance()


    def update_row_subtotals(self):

        subtotal = 0

        for row in range(
            self.sales_table.rowCount()
        ):

            price_item = self.sales_table.item(
                row,
                2
            )

            quantity_spin = self.sales_table.cellWidget(
                row,
                1
            )

            if not price_item or not quantity_spin:
                continue

            try:

                price = float(
                    price_item.text()
                )

                quantity = (
                    quantity_spin.value()
                )

                row_subtotal = (
                    price * quantity
                )

                subtotal += row_subtotal

                subtotal_item = (
                    self.sales_table.item(
                        row,
                        3
                    )
                )

                if subtotal_item:

                    subtotal_item.setText(
                        f"{row_subtotal:.2f}"
                    )

            except ValueError:

                continue

        return subtotal

    def payment_method_changed(
        self,
        method
    ):

        if method == "Credit":

            self.cash_received_spin.setValue(
                0
            )

            self.cash_received_spin.setEnabled(
                False
            )

        else:

            self.cash_received_spin.setEnabled(
                True
            )

        self.update_balance()


    def update_balance(self):

        subtotal = self.update_row_subtotals()

        labour_amount = float(
            self.labour_spin.value()
        )

        discount = float(
            self.discount_spin.value()
        )

    

        if discount > (subtotal + labour_amount):

            total = 0

        else:

            total = subtotal + labour_amount - discount

        payment_method = (
            self.payment_combo.currentText()
        )

        cash_received = float(
            self.cash_received_spin.value()
        )

        if payment_method == "Credit":

            balance = total
            change = 0

        else:

            balance = max(
                0,
                total - cash_received
            )

            change = max(
                0,
                cash_received - total
            )

      
        self.subtotal_label.setText(
            f"Subtotal: Rs. {subtotal:,.2f}"
        )

        self.labour_label.setText(
            f"Labour Charges: Rs. {labour_amount:,.2f}"
        )

        self.discount_label.setText(
            f"Discount: Rs. {discount:,.2f}"
        )

        self.total_label.setText(
            f"Total: Rs. {total:,.2f}"
        )

        self.balance_label.setText(
            f"Balance: Rs. {balance:,.2f}"
        )

        self.change_label.setText(
            f"Change: Rs. {change:,.2f}"
        )

   
    def validate_bill(self):

        if self.sales_table.rowCount() == 0:

            QMessageBox.warning(
                self,
                "Empty Bill",
                "Bill must contain at least one product."
            )

            return False

        subtotal = 0

        for row in range(
            self.sales_table.rowCount()
        ):

            price_item = self.sales_table.item(
                row,
                2
            )

            quantity_spin = self.sales_table.cellWidget(
                row,
                1
            )

            product_id_item = self.sales_table.item(
                row,
                5
            )

            if (
                not price_item
                or not quantity_spin
                or not product_id_item
            ):

                QMessageBox.warning(
                    self,
                    "Invalid Product",
                    "One or more products contain invalid data."
                )

                return False

            try:

                price = float(
                    price_item.text()
                )

                quantity = int(
                    quantity_spin.value()
                )

                product_id = int(
                    product_id_item.text()
                )

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Invalid Data",
                    "Product price, quantity or ID is invalid."
                )

                return False

            if quantity <= 0:

                QMessageBox.warning(
                    self,
                    "Invalid Quantity",
                    "Quantity must be greater than zero."
                )

                return False

            product = self.db.get_product(
                product_id
            )

            if not product:

                QMessageBox.warning(
                    self,
                    "Product Missing",
                    "A product in this bill no longer exists."
                )

                return False

            subtotal += (
                price * quantity
            )

        labour_amount = float(
            self.labour_spin.value()
        )

        if labour_amount < 0:
            QMessageBox.warning(
                self,
                "Invalid Labour Charges",
                "Labour charges cannot be negative."
            )
            return False

        discount = float(
            self.discount_spin.value()
        )

        if discount < 0:

            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Discount cannot be negative."
            )

            return False

        if discount > (subtotal + labour_amount):

            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Discount cannot be greater than subtotal + labour charges."
            )

            return False

        total = max(
            0,
            subtotal + labour_amount - discount
        )

        payment_method = (
            self.payment_combo.currentText()
        )

        cash_received = float(
            self.cash_received_spin.value()
        )
        if payment_method == "Credit":

            return True

       

        if cash_received < total:

            QMessageBox.warning(
                self,
                "Insufficient Cash",
                f"Received cash is less than total amount.\n\n"
                f"Total: Rs. {total:,.2f}\n"
                f"Received: Rs. {cash_received:,.2f}"
            )

            return False

        return True

   

    def save_changes(self):

       

        if not self.validate_bill():
            return

        cart_items = []

       
        for row in range(
            self.sales_table.rowCount()
        ):

            product_name_item = (
                self.sales_table.item(row, 0)
            )

            price_item = (
                self.sales_table.item(row, 2)
            )

            product_id_item = (
                self.sales_table.item(row, 5)
            )

            quantity_spin = (
                self.sales_table.cellWidget(row, 1)
            )

            if (
                not product_name_item
                or not price_item
                or not product_id_item
                or not quantity_spin
            ):
                continue

            try:

                product_name = (
                    product_name_item.text()
                )

                price = float(
                    price_item.text()
                )

                product_id = int(
                    product_id_item.text()
                )

                quantity = int(
                    quantity_spin.value()
                )

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Invalid Data",
                    "Could not read one of the products."
                )

                return

            cart_items.append({
                "product_id": product_id,
                "name": product_name,
                "price": price,
                "quantity": quantity
            })

        if not cart_items:

            QMessageBox.warning(
                self,
                "Empty Bill",
                "Bill must contain at least one product."
            )

            return

       

        subtotal = sum(
            item["price"] * item["quantity"]
            for item in cart_items
        )

        labour_amount = float(
            self.labour_spin.value()
        )

        discount = float(
            self.discount_spin.value()
        )

        total_amount = max(
            0,
            subtotal + labour_amount - discount
        )

        payment_method = (
            self.payment_combo.currentText()
        )

    

        customer_name = self.customer_name_input.text().strip()

        customer_phone = self.customer_phone_input.text().strip()

        if not customer_name:
            customer_name = "Walk-in Customer"

        cash_received = float(
            self.cash_received_spin.value()
        )

        if payment_method == "Credit":

            cash_received = 0
        reply = QMessageBox.question(
            self,
            "Confirm Changes",
            f"Update invoice {self.sale['invoice_number']}?\n\n"
            f"Subtotal: Rs. {subtotal:,.2f}\n"
            f"Labour Charges: Rs. {labour_amount:,.2f}\n"
            f"Discount: Rs. {discount:,.2f}\n"
            f"Total: Rs. {total_amount:,.2f}\n"
            f"Payment: {payment_method}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

    

        try:

            success = self.db.update_sale(
                sale_id=self.sale_id,
                cart_items=cart_items,
                total_amount=total_amount,
                payment_method=payment_method,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_id=None,
                discount=discount,
                cash_received=cash_received,
                labour_amount=labour_amount
            )

            if not success:

                QMessageBox.warning(
                    self,
                    "Update Failed",
                    "Bill update nahi ho saki."
                )

                return
            
        
            try:

                items = self.db.get_sale_items(
                    self.sale_id
                )

                cart_items = []

                for item in items:

                    cart_items.append({
                        "product_id": item["product_id"],
                        "name": item["product_name"],
                        "price": item["price"],
                        "quantity": item["quantity"]
                    })

              
                updated_sale = self.db.get_sale_by_id(
                    self.sale_id
                )

                subtotal = sum(
                    float(item["price"]) * int(item["quantity"])
                    for item in cart_items
                )

                updated_labour = float(
                    updated_sale["labour_amount"] or 0
                )

                updated_discount = float(
                    updated_sale["discount"] or 0
                )

                updated_total = float(
                    updated_sale["total_amount"] or 0
                )

                updated_cash = float(
                    updated_sale["cash_received"] or 0
                )

                updated_payment = (
                    updated_sale["payment_method"] or "Cash"
                )

                updated_customer_name = (
                    updated_sale["customer_name"]
                    or "Walk-in Customer"
                )

                updated_customer_phone = (
                    updated_sale["customer_phone"]
                    or ""
                )
                updated_paper_size = (
                    updated_sale["paper_size"]
                    or "A4"
                )

                generate_invoice(
                    invoice_number=updated_sale["invoice_number"],
                    cart_items=cart_items,
                    total_amount=updated_total,
                    payment_method=updated_payment,
                    customer_name=updated_customer_name,
                    customer_phone=updated_customer_phone,
                    subtotal=subtotal,
                    labour_amount=updated_labour,
                    discount=updated_discount,
                    cash_received=updated_cash,
                    change=max(
                        0,
                        updated_cash - updated_total
                    ),
                    paper_size=updated_paper_size
                )

            except Exception as pdf_error:

                QMessageBox.warning(
                    self,
                    "PDF Warning",
                    f"Bill updated, but PDF could not be regenerated.\n\n"
                    f"{pdf_error}"
                )

            QMessageBox.information(
                self,
                "Success",
                f"Invoice {self.sale['invoice_number']} "
                f"updated successfully."
            )

            self.accept()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Update Error",
                str(error)
            )