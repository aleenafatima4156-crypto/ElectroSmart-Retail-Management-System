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
    QPushButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QInputDialog,
)
from PySide6.QtCore import Qt

import os
import sqlite3

from database.database_manager import DatabaseManager


class ProductsPage(QWidget):
    """Products management page for the Electrical Shop Management System."""

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()
        self.setup_ui()
        self.load_products()

    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 22, 28, 22)
        main_layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Products Management")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Manage products, prices and stock levels")
        subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.add_button = apply_professional_icon(QPushButton('Add Product'), 'fa5s.plus-circle', '#FFFFFF')
        self.add_button.setObjectName("primaryButton")
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setFixedHeight(42)
        self.add_button.clicked.connect(self.show_add_form)

        self.delete_button = apply_professional_icon(QPushButton('Delete Selected'), 'fa5s.trash-alt', '#FFFFFF')
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setFixedHeight(42)
        self.delete_button.clicked.connect(self.delete_selected_product)

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(self.delete_button)
        header.addWidget(self.add_button)

        main_layout.addLayout(header)

        self.form_frame = QFrame()
        self.form_frame.setObjectName("card")
        self.form_frame.setVisible(False)
        self.form_frame.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        form_layout = QVBoxLayout(self.form_frame)
        form_layout.setContentsMargins(18, 14, 18, 14)
        form_layout.setSpacing(8)

        form_header = QHBoxLayout()

        form_title = QLabel("Add New Product")
        form_title.setObjectName("cardTitle")

        form_hint = QLabel("Enter product information below")
        form_hint.setObjectName("cardHint")

        form_header.addWidget(form_title)
        form_header.addSpacing(12)
        form_header.addWidget(form_hint)
        form_header.addStretch()

        form_layout.addLayout(form_header)

        fields_grid = QGridLayout()
        fields_grid.setHorizontalSpacing(18)
        fields_grid.setVerticalSpacing(5)
        fields_grid.setColumnStretch(0, 1)
        fields_grid.setColumnStretch(1, 1)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Royal Ceiling Fan")

        self.category_input = QComboBox()
        self.category_input.addItems([
            "Fans",
            "Capacitors",
            "Switches",
            "Sockets",
            "Wires & Cables",
            "LED Lights",
            "Circuit Breakers",
            "Other",
        ])
        self.category_input.currentTextChanged.connect(self.handle_category_change)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("e.g. Pak Fan")

        self.unit_input = QComboBox()
        self.unit_input.addItems([
            "Piece",
            "Meter",
            "Box",
            "Roll",
            "Pack",
        ])

        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 99999999.99)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setPrefix("Rs. ")
        self.purchase_price_input.setAlignment(Qt.AlignLeft)
        self.purchase_price_input.setButtonSymbols(
            QDoubleSpinBox.NoButtons
        )

        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setRange(0, 99999999.99)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setPrefix("Rs. ")
        self.selling_price_input.setAlignment(Qt.AlignLeft)
        self.selling_price_input.setButtonSymbols(
            QDoubleSpinBox.NoButtons
        )

        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        self.stock_input.setAlignment(Qt.AlignLeft)
        self.stock_input.setButtonSymbols(QSpinBox.NoButtons)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 999999)
        self.min_stock_input.setAlignment(Qt.AlignLeft)
        self.min_stock_input.setButtonSymbols(QSpinBox.NoButtons)

    
        for field in (
            self.name_input,
            self.category_input,
            self.brand_input,
            self.unit_input,
            self.purchase_price_input,
            self.selling_price_input,
            self.stock_input,
            self.min_stock_input,
        ):
            field.setFixedHeight(28)

    
        self._add_field(fields_grid, 0, 0, "Product Name", self.name_input)
        self._add_field(fields_grid, 0, 1, "Category", self.category_input)

        
        self._add_field(fields_grid, 1, 0, "Brand", self.brand_input)
        self._add_field(fields_grid, 1, 1, "Unit", self.unit_input)

        
        self._add_field(
            fields_grid, 2, 0, "Purchase Price", self.purchase_price_input
        )
        self._add_field(
            fields_grid, 2, 1, "Selling Price", self.selling_price_input
        )

        
        self._add_field(
            fields_grid, 3, 0, "Stock Quantity", self.stock_input
        )
        self._add_field(
            fields_grid, 3, 1, "Minimum Stock Alert", self.min_stock_input
        )

        form_layout.addLayout(fields_grid)

        
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_button = apply_professional_icon(QPushButton('Cancel'), 'fa5s.times', '#1E293B')
        cancel_button.setObjectName("secondaryButton")
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.setFixedSize(110, 36)
        cancel_button.clicked.connect(self.hide_add_form)

        save_button = apply_professional_icon(QPushButton('Save Product'), 'fa5s.save', '#FFFFFF')
        save_button.setObjectName("successButton")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.setFixedSize(130, 36)
        save_button.clicked.connect(self.save_product)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        form_layout.addLayout(buttons)
        main_layout.addWidget(self.form_frame)

        search_frame = QFrame()
        search_frame.setObjectName("searchCard")

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 10, 14, 10)
        search_layout.setSpacing(12)

        search_label = QLabel("Search Product")
        search_label.setObjectName("searchLabel")

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText(
            "Search by product name, category or brand..."
        )
        self.product_search.setClearButtonEnabled(True)
        self.product_search.textChanged.connect(self.search_products)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.product_search, 1)

        main_layout.addWidget(search_frame)

    
        table_frame = QFrame()
        table_frame.setObjectName("tableCard")

        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Product Name",
            "Category",
            "Brand",
            "Purchase Price",
            "Selling Price",
            "Stock",
            "Min Stock",
            "Unit",
        ])

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)
        self.table.setMinimumHeight(180)

        header_view = self.table.horizontalHeader()
        header_view.setDefaultAlignment(Qt.AlignCenter)
        header_view.setMinimumSectionSize(70)

        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(8, QHeaderView.ResizeToContents)

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_frame, 1)

        self.setStyleSheet("""
            QWidget {
                background: #F1F5F9;
                color: #1E293B;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLabel#pageTitle {
                background: transparent;
                color: #172033;
                font-size: 27px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                background: transparent;
                color: #64748B;
                font-size: 12px;
            }

            QFrame#card,
            QFrame#searchCard,
            QFrame#tableCard {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }

            QLabel#cardTitle {
                background: transparent;
                color: #172033;
                font-size: 17px;
                font-weight: 700;
            }

            QLabel#cardHint {
                background: transparent;
                color: #94A3B8;
                font-size: 12px;
            }

            QLabel#fieldLabel {
                background: transparent;
                color: #334155;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#searchLabel {
                background: transparent;
                color: #334155;
                font-size: 13px;
                font-weight: 600;
                padding-left: 2px;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 5px 10px;
                min-height: 20px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #3B82F6;
            }

            QComboBox::drop-down {
                border: none;
                width: 28px;
            }

            QPushButton#primaryButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#primaryButton:hover {
                background: #1D4ED8;
            }

            QPushButton#dangerButton {
                background: #DC2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#dangerButton:hover {
                background: #B91C1C;
            }

            QPushButton#dangerButton:disabled {
                background: #CBD5E1;
                color: #64748B;
            }

            QPushButton#successButton {
                background: #16A34A;
                color: white;
                border: none;
                border-radius: 7px;
                font-weight: 700;
            }

            QPushButton#successButton:hover {
                background: #15803D;
            }

            QPushButton#secondaryButton {
                background: #E2E8F0;
                color: #334155;
                border: none;
                border-radius: 7px;
                font-weight: 600;
            }

            QPushButton#secondaryButton:hover {
                background: #CBD5E1;
            }

            QTableWidget {
                background: #FFFFFF;
                color: #334155;
                border: none;
                border-radius: 12px;
                font-size: 12px;
                outline: none;
            }

            QTableWidget::item {
                padding: 7px;
                border-bottom: 1px solid #F1F5F9;
            }

            QTableWidget::item:selected {
                background: #DBEAFE;
                color: #1E3A8A;
            }

            QHeaderView::section {
                background: #1E293B;
                color: #FFFFFF;
                padding: 10px 8px;
                border: none;
                font-size: 12px;
                font-weight: 700;
            }

            QScrollBar:vertical {
                width: 9px;
                background: #F8FAFC;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 30px;
            }
        """)

    def _add_field(self, grid, row, column, label_text, widget):
        container = QWidget()
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")

        layout.addWidget(label)
        layout.addWidget(widget)

        grid.addWidget(container, row, column)


    def show_add_form(self):
        self.form_frame.setVisible(True)
        self.name_input.setFocus()
        self.add_button.setEnabled(False)

    def hide_add_form(self):
        self.form_frame.setVisible(False)
        self.add_button.setEnabled(True)

    def handle_category_change(self, category):
        """Ask for a custom category when 'Other' is selected."""
        if category != "Other":
            return

        custom_category, ok = QInputDialog.getText(
            self,
            "Custom Category",
            "Please enter the category manually:"
        )

        if ok and custom_category.strip():
            custom_category = custom_category.strip()

           
            other_index = self.category_input.findText("Other")
            if self.category_input.findText(custom_category) == -1:
                self.category_input.insertItem(other_index, custom_category)

            self.category_input.setCurrentText(custom_category)
        else:
         
            self.category_input.setCurrentIndex(0)

    def save_product(self):
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a product name.",
            )
            self.name_input.setFocus()
            return

        purchase_price = self.purchase_price_input.value()
        selling_price = self.selling_price_input.value()

        if selling_price < purchase_price:
            QMessageBox.warning(
                self,
                "Invalid Price",
                "Selling price cannot be lower than purchase price.",
            )
            self.selling_price_input.setFocus()
            return

        category = self.category_input.currentText()
        brand = self.brand_input.text().strip()
        stock = self.stock_input.value()
        min_stock = self.min_stock_input.value()
        unit = self.unit_input.currentText()

        try:
            self.db.add_product(
                name,
                category,
                brand,
                purchase_price,
                selling_price,
                stock,
                min_stock,
                unit,
            )

            QMessageBox.information(
                self,
                "Product Added",
                "Product added successfully!",
            )

            self.clear_form()
            self.load_products()
            self.hide_add_form()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Product Error",
                f"Could not add product.\n\n{error}",
            )

    def clear_form(self):
        self.name_input.clear()
        self.brand_input.clear()
        self.category_input.setCurrentIndex(0)
        self.unit_input.setCurrentIndex(0)
        self.purchase_price_input.setValue(0)
        self.selling_price_input.setValue(0)
        self.stock_input.setValue(0)
        self.min_stock_input.setValue(0)

  
    def load_products(self):
        try:
            products = self.db.get_products()
            self.display_products(products)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Could not load products.\n\n{error}",
            )

    def display_products(self, products):
        columns = [
            "id",
            "name",
            "category",
            "brand",
            "purchase_price",
            "selling_price",
            "stock",
            "min_stock",
            "unit",
        ]

        self.table.setRowCount(0)
        self.table.setRowCount(len(products))

        for row_index, product in enumerate(products):
            for column_index, key in enumerate(columns):
                value = product[key]

                if key in ("purchase_price", "selling_price"):
                    text = f"Rs. {float(value or 0):,.2f}"
                else:
                    text = str(value if value is not None else "")

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

          
            stock = int(product["stock"] or 0)
            min_stock = int(product["min_stock"] or 0)

            if stock <= min_stock:
                for column in range(self.table.columnCount()):
                    item = self.table.item(row_index, column)
                    if item:
                        item.setToolTip("Low stock: at or below minimum stock level.")

    def delete_selected_product(self):
        """Delete the currently selected product safely from the products table."""
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Product Selected",
                "Please select a product from the table first.",
            )
            return

        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)

        if not id_item or not name_item:
            QMessageBox.warning(
                self,
                "Delete Error",
                "Could not identify the selected product.",
            )
            return

        try:
            product_id = int(id_item.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Delete Error",
                "Invalid product ID.",
            )
            return

        product_name = name_item.text().strip()

        answer = QMessageBox.question(
            self,
            "Delete Product",
            f'Are you sure you want to delete "{product_name}"?\\n\\n'
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, "database", "electrosmart.db")

        connection = None
        try:
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")

            connection = sqlite3.connect(db_path)
            connection.execute("PRAGMA foreign_keys = ON")
            cursor = connection.cursor()

            sale_count = 0
            purchase_count = 0

            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM sale_items WHERE product_id = ?",
                    (product_id,),
                )
                sale_count = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM purchase_items WHERE product_id = ?",
                    (product_id,),
                )
                purchase_count = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                pass

            if sale_count > 0 or purchase_count > 0:
                QMessageBox.warning(
                    self,
                    "Cannot Delete Product",
                    f'"{product_name}" cannot be deleted because it is already used '
                    "in sales or purchase history.\\n\\n"
                    "You can keep it for historical records instead.",
                )
                return

            cursor.execute(
                "DELETE FROM products WHERE id = ?",
                (product_id,),
            )

            if cursor.rowcount == 0:
                connection.rollback()
                QMessageBox.warning(
                    self,
                    "Delete Error",
                    "The selected product no longer exists in the database.",
                )
                self.load_products()
                return

            connection.commit()

            QMessageBox.information(
                self,
                "Product Deleted",
                f'"{product_name}" has been deleted successfully.',
            )

            self.load_products()

        except sqlite3.IntegrityError:
            if connection:
                connection.rollback()
            QMessageBox.warning(
                self,
                "Cannot Delete Product",
                "This product is linked with existing records and cannot be deleted.",
            )
        except Exception as error:
            if connection:
                connection.rollback()
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Could not delete product.\\n\\n{error}",
            )
        finally:
            if connection:
                connection.close()

    def search_products(self):
        text = self.product_search.text().lower().strip()

        try:
            products = self.db.get_products()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Search Error",
                f"Could not search products.\n\n{error}",
            )
            return

        if not text:
            self.display_products(products)
            return

        filtered_products = []

        for product in products:
            name = str(product["name"] or "").lower()
            category = str(product["category"] or "").lower()
            brand = str(product["brand"] or "").lower()

            if (
                text in name
                or text in category
                or text in brand
            ):
                filtered_products.append(product)

        self.display_products(filtered_products)
