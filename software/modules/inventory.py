
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
    QFrame,
    QSpinBox,
    QMessageBox
)

from PySide6.QtCore import Qt

from database.database_manager import DatabaseManager


class InventoryPage(QWidget):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()

        self.setup_ui()
        self.load_inventory()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            30, 25, 30, 25
        )

        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()

        title = QLabel("Inventory Management")

        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1E293B;
        """)

        refresh_button = apply_professional_icon(QPushButton('Refresh'), 'fa5s.sync-alt', '#FFFFFF')

        refresh_button.clicked.connect(
            self.load_inventory
        )

        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)

        main_layout.addLayout(header_layout)


        cards_layout = QHBoxLayout()

        self.total_products_label = self.create_card(
            cards_layout,
            "Total Products",
            "0"
        )

        self.total_stock_label = self.create_card(
            cards_layout,
            "Total Stock Units",
            "0"
        )

        self.total_stock_amount_label = self.create_card(
            cards_layout,
            "Total Stock Amount",
            "Rs. 0.00"
        )

        self.low_stock_label = self.create_card(
            cards_layout,
            "Low Stock",
            "0"
        )

        self.out_stock_label = self.create_card(
            cards_layout,
            "Out of Stock",
            "0"
        )

        main_layout.addLayout(cards_layout)


        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels([
            "Product",
            "Category",
            "Current Stock",
            "Min Stock",
            "Unit",
            "Status",
            "Update Stock"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-size: 13px;
            }

            QHeaderView::section {
                background-color: #1E293B;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)

        main_layout.addWidget(self.table)

    def create_card(self, layout, title, value):

        card = QFrame()

        card.setFixedHeight(100)

        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)

        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)

        title_label.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
        """)

        value_label = QLabel(value)

        value_label.setStyleSheet("""
            color: #1E293B;
            font-size: 24px;
            font-weight: bold;
        """)

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        layout.addWidget(card)

        return value_label


    def load_inventory(self):

        products = self.db.get_products()

        self.table.setRowCount(
            len(products)
        )

        total_stock = 0
        total_stock_amount = 0.0
        low_stock = 0
        out_of_stock = 0

        for row, product in enumerate(products):

            stock = product["stock"]
            minimum = product["min_stock"]

            purchase_price = float(product["purchase_price"] or 0)
            total_stock += stock
            total_stock_amount += stock * purchase_price

            if stock == 0:
                status = "OUT OF STOCK"
                out_of_stock += 1

            elif stock <= minimum:
                status = "LOW STOCK"
                low_stock += 1

            else:
                status = "IN STOCK"

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(
                    product["name"]
                )
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    product["category"]
                )
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(stock)
                )
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    str(minimum)
                )
            )

            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    product["unit"]
                )
            )

            status_item = QTableWidgetItem(status)

            status_item.setTextAlignment(
                Qt.AlignCenter
            )

            if status == "OUT OF STOCK":
                status_item.setBackground(
                    Qt.red
                )

                status_item.setForeground(
                    Qt.white
                )

            elif status == "LOW STOCK":
                status_item.setBackground(
                    Qt.yellow
                )

            else:
                status_item.setBackground(
                    Qt.green
                )

            self.table.setItem(
                row,
                5,
                status_item
            )

            update_button = apply_professional_icon(QPushButton('Update'), 'fa5s.edit', '#FFFFFF')

            update_button.clicked.connect(
                lambda checked=False,
                p=product:
                self.update_stock(p)
            )

            update_button.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    color: white;
                    border: none;
                    padding: 7px;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)

            self.table.setCellWidget(
                row,
                6,
                update_button
            )

        self.total_products_label.setText(
            str(len(products))
        )

        self.total_stock_label.setText(
            str(total_stock)
        )

        self.total_stock_amount_label.setText(
            f"Rs. {total_stock_amount:,.2f}"
        )

        self.low_stock_label.setText(
            str(low_stock)
        )

        self.out_stock_label.setText(
            str(out_of_stock)
        )

    def update_stock(self, product):

        current_stock = product["stock"]

        from PySide6.QtWidgets import QInputDialog

        new_stock, ok = QInputDialog.getInt(
            self,
            "Update Stock",
            f"Enter new stock for {product['name']}:",
            current_stock,
            0,
            999999,
            1
        )

        if not ok:
            return

        try:

            self.db.update_product_stock(
                product["id"],
                new_stock
            )

            QMessageBox.information(
                self,
                "Stock Updated",
                f"{product['name']} stock updated to "
                f"{new_stock}."
            )

            self.load_inventory()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                str(error)
            )
            