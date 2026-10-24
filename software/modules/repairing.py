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

import os
import urllib.parse
import html
import webbrowser
import shutil
from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGroupBox,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QTextEdit, QDialogButtonBox, QScrollArea
)

from database.database_manager import DatabaseManager



SHOP_DEFAULT = "Nadeem Shahanvi Electrical & Electronics Care Centre"
SHOP_DEALS = "We Deals in All Kind of Electrical & Electronics Repairing work. Industrial Auto Control, ATS, LT Panel, PLC , VFD, UPS, Stabilizer. All Types Of Motor Winding and other All types of Home Amplinces  Repairing and Fixing"
SHOP_PHONE = "Cell: 0302-4420051, 0300-4644413"
SHOP_ADDRESS = "Address: Shop No 02 Plot No 09 Rehmat Block Sheraz Town Bagrian Lahore"

REPAIRING_TERMS = [
    "1. No warranty is provided on electronic parts unless specifically mentioned on the repair receipt.",
    "2. Replaced/old parts will not be returned to the customer.",
    "3. The customer will be informed before any major repair or replacement of parts.",
    "4. 50% advance payment is required before starting the repair work.",
    "5. Home service/visit charges will be applicable separately, where required.",
    "6. We are not responsible for any damage to components or the appliance caused by pre-existing faults, hidden defects, or during the repair process.",
    "7. The appliance must be collected within 15 days after completion of the repair. After 15 days, the shop will not be responsible for the appliance or any accessories.",
    "8. Repair charges are applicable for inspection, diagnosis, labor, and replaced parts as agreed with the customer.",
]


class RepairItemDialog(QDialog):
    def __init__(self, parent=None, item=None, title="Add Requirement"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        form = QFormLayout(self)

        self.description = QLineEdit()
        self.description.setPlaceholderText("e.g. Capacitor 10µF, wire, switch, cleaning")
        self.qty = QSpinBox()
        self.qty.setRange(1, 100000)
        self.qty.setValue(1)
        self.unit_cost = QDoubleSpinBox()
        self.unit_cost.setRange(0, 100000000)
        self.unit_cost.setDecimals(2)
        self.unit_cost.setPrefix("Rs. ")

        form.addRow("Requirement / Product:", self.description)
        form.addRow("Quantity:", self.qty)
        form.addRow("Estimated Unit Cost:", self.unit_cost)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        if item:
            self.description.setText(str(item.get("description", "")))
            self.qty.setValue(int(item.get("quantity", 1)))
            self.unit_cost.setValue(float(item.get("unit_cost", 0) or 0))

    def validate_and_accept(self):
        if not self.description.text().strip():
            QMessageBox.warning(self, "Required", "Please enter the product/requirement.")
            return
        self.accept()

    def values(self):
        return {
            "description": self.description.text().strip(),
            "quantity": self.qty.value(),
            "unit_cost": self.unit_cost.value(),
        }


class ActualBillDialog(QDialog):
    def __init__(self, parent, repair, items):
        super().__init__(parent)
        self.setWindowTitle(f"Create Actual Bill - {repair['repair_number']}")
        self.setMinimumSize(850, 650)
        self.repair = repair
        self.items = [dict(x) for x in items]

        outer = QVBoxLayout(self)
        info = QLabel(
            f"<b>Repair:</b> {repair['repair_number']} &nbsp;&nbsp; "
            f"<b>Customer:</b> {repair['customer_name']} &nbsp;&nbsp; "
            f"<b>Item:</b> {repair['item_name']}"
        )
        outer.addWidget(info)

        group = QGroupBox("Actual Materials / Work Used")
        gl = QVBoxLayout(group)
        self.table = QTableWidget(0, 5)
        self.table.setMinimumHeight(180)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalHeaderLabels(["Requirement / Product", "Qty", "Unit Cost", "Total", "Remove"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        gl.addWidget(self.table)
        row = QHBoxLayout()
        add = apply_professional_icon(QPushButton('Add Item'), 'fa5s.plus', '#FFFFFF')
        add.clicked.connect(self.add_item)
        edit = apply_professional_icon(QPushButton('Edit Selected'), 'fa5s.pen', '#FFFFFF')
        edit.clicked.connect(self.edit_item)
        row.addWidget(add)
        row.addWidget(edit)
        row.addStretch()
        gl.addLayout(row)
        outer.addWidget(group)

        charges = QGroupBox("Actual Charges")
        cg = QGridLayout(charges)
        self.labour = QDoubleSpinBox(); self.labour.setRange(0, 100000000); self.labour.setDecimals(2); self.labour.setPrefix("Rs. ")
        self.other = QDoubleSpinBox(); self.other.setRange(0, 100000000); self.other.setDecimals(2); self.other.setPrefix("Rs. ")
        self.discount = QDoubleSpinBox(); self.discount.setRange(0, 100000000); self.discount.setDecimals(2); self.discount.setPrefix("Rs. ")
        self.payment = QComboBox(); self.payment.addItems(["Cash", "JazzCash", "EasyPaisa", "Bank Transfer", "Card", "Unpaid"])
        self.received = QDoubleSpinBox(); self.received.setRange(0, 100000000); self.received.setDecimals(2); self.received.setPrefix("Rs. ")
        self.notes = QLineEdit(); self.notes.setPlaceholderText("Actual work / warranty / delivery notes")
        cg.addWidget(QLabel("Labour Charges:"), 0, 0); cg.addWidget(self.labour, 0, 1)
        cg.addWidget(QLabel("Other Charges:"), 0, 2); cg.addWidget(self.other, 0, 3)
        cg.addWidget(QLabel("Discount:"), 1, 0); cg.addWidget(self.discount, 1, 1)
        cg.addWidget(QLabel("Payment:"), 1, 2); cg.addWidget(self.payment, 1, 3)
        cg.addWidget(QLabel("Amount Received:"), 2, 0); cg.addWidget(self.received, 2, 1)
        cg.addWidget(QLabel("Notes:"), 2, 2); cg.addWidget(self.notes, 2, 3)
        outer.addWidget(charges)

        self.total_label = QLabel("Actual Total: Rs. 0.00")
        self.total_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        outer.addWidget(self.total_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)
        self.refresh_table()
        self.payment_changed(self.payment.currentText())
        self.labour.valueChanged.connect(self.recalculate)
        self.other.valueChanged.connect(self.recalculate)
        self.discount.valueChanged.connect(self.recalculate)
        self.payment.currentTextChanged.connect(self.payment_changed)

    def refresh_table(self):
        self.table.setRowCount(0)
        for item in self.items:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(item['description'])))
            self.table.setItem(r, 1, QTableWidgetItem(str(item['quantity'])))
            self.table.setItem(r, 2, QTableWidgetItem(f"Rs. {float(item['unit_cost']):,.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"Rs. {float(item['quantity']) * float(item['unit_cost']):,.2f}"))
            remove = apply_professional_icon(QPushButton('Remove'), 'fa5s.trash-alt', '#FFFFFF')
            remove.clicked.connect(lambda _, row=r: self.remove_item(row))
            self.table.setCellWidget(r, 4, remove)
        self.recalculate()

    def add_item(self):
        dlg = RepairItemDialog(self)
        if dlg.exec() == QDialog.Accepted:
            item = dlg.values()
            self.items.append(item)
            self.refresh_table()
            if self.table.rowCount() > 0:
                self.table.selectRow(self.table.rowCount() - 1)
                self.table.scrollToBottom()

    def edit_item(self):
        r = self.table.currentRow()
        if r < 0 or r >= len(self.items):
            QMessageBox.information(self, "Select Item", "Please select an item first.")
            return
        dlg = RepairItemDialog(self, self.items[r], "Edit Actual Item")
        if dlg.exec() == QDialog.Accepted:
            self.items[r] = dlg.values(); self.refresh_table()

    def remove_item(self, row):
        if 0 <= row < len(self.items):
            self.items.pop(row); self.refresh_table()

    def payment_changed(self, method):
        if method == "Unpaid":
            self.received.setValue(0)
            self.received.setEnabled(False)
        else:
            self.received.setEnabled(True)

    def recalculate(self):
        materials = sum(float(i['quantity']) * float(i['unit_cost']) for i in self.items)
        total = max(0, materials + self.labour.value() + self.other.value() - self.discount.value())
        self.total_label.setText(f"Actual Total: Rs. {total:,.2f}")

    def validate_and_accept(self):
        if not self.items and self.labour.value() <= 0 and self.other.value() <= 0:
            QMessageBox.warning(self, "Empty Bill", "Add at least one item or a labour/other charge.")
            return

        total = self.values()["total_amount"]
        if self.payment.currentText() == "Unpaid":
            self.received.setValue(0)
        elif self.received.value() > total:
            QMessageBox.warning(
                self,
                "Invalid Amount",
                f"Amount received cannot be greater than the bill total (Rs. {total:,.2f})."
            )
            return

        self.accept()

    def values(self):
        materials = sum(float(i['quantity']) * float(i['unit_cost']) for i in self.items)
        total = max(0, materials + self.labour.value() + self.other.value() - self.discount.value())
        return {
            "items": self.items,
            "labour_amount": self.labour.value(),
            "other_charges": self.other.value(),
            "discount": self.discount.value(),
            "total_amount": total,
            "payment_method": self.payment.currentText(),
            "amount_received": self.received.value(),
            "notes": self.notes.text().strip(),
        }


class RepairingPage(QWidget):
    """Repair & Maintenance workflow: raw estimate -> customer decision -> actual bill."""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_id = None
        self.estimate_items = []
        self.settings = None
        self.last_actual_pdf_path = None
        self.build_ui()
        self.refresh_jobs()
        self.new_repair()

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(25, 20, 25, 20)
        outer.setSpacing(12)

        title = QLabel("Repairing & Maintenance")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B;")
        outer.addWidget(title)
        sub = QLabel("Create a repair estimate, send it to the customer, record approval/rejection, then generate the actual bill.")
        sub.setStyleSheet("color: #64748B; font-size: 13px;")
        outer.addWidget(sub)

        toolbar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search repair no, customer, phone, item or serial...")
        self.search.textChanged.connect(self.refresh_jobs)
        toolbar.addWidget(self.search, 1)
        new_btn = apply_professional_icon(QPushButton('New Repair Job'), 'fa5s.plus-circle', '#FFFFFF'); new_btn.clicked.connect(self.new_repair); toolbar.addWidget(new_btn)
        refresh = apply_professional_icon(QPushButton('Refresh'), 'fa5s.sync-alt', '#FFFFFF'); refresh.clicked.connect(self.refresh_jobs); toolbar.addWidget(refresh)
        outer.addLayout(toolbar)

        self.jobs_table = QTableWidget(0, 8)
        self.jobs_table.setHorizontalHeaderLabels(["Repair No.", "Customer", "Item", "Received", "Estimate", "Status", "Actual Bill", "Open"])
        self.jobs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.jobs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.jobs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.jobs_table.cellDoubleClicked.connect(self.open_selected)
        self.jobs_table.setMinimumHeight(180)
        self.jobs_table.setMaximumHeight(260)
        outer.addWidget(self.jobs_table)

        self.editor = QFrame()
        self.editor.setStyleSheet("QFrame { background: white; border-radius: 10px; }")
        eg = QGridLayout(self.editor)
        eg.setContentsMargins(15, 15, 15, 15)

        self.repair_no = QLabel("New")
        self.customer = QLineEdit(); self.customer.setPlaceholderText("Customer name")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("03XXXXXXXXX")
        self.item_name = QLineEdit(); self.item_name.setPlaceholderText("e.g. AC, TV, Fan, Washing Machine")
        self.item_type = QLineEdit(); self.item_type.setPlaceholderText("Item type")
        self.brand = QLineEdit(); self.brand.setPlaceholderText("Brand")
        self.model = QLineEdit(); self.model.setPlaceholderText("Model")
        self.serial = QLineEdit(); self.serial.setPlaceholderText("Serial number")
        self.received_date = QDateEdit(); self.received_date.setCalendarPopup(True); self.received_date.setDate(QDate.currentDate())
        self.expected_date = QDateEdit(); self.expected_date.setCalendarPopup(True); self.expected_date.setDate(QDate.currentDate().addDays(2))
        self.condition = QTextEdit(); self.condition.setPlaceholderText("Condition of item when received")
        self.problem = QTextEdit(); self.problem.setPlaceholderText("Customer's reported problem")
        self.fault = QTextEdit(); self.fault.setPlaceholderText("What is faulty / defective? Enter details manually")
        self.technician = QTextEdit(); self.technician.setPlaceholderText("Technician notes / diagnosis / recommended work")

        fields = [
            ("Repair No.", self.repair_no, 0, 0), ("Customer Name", self.customer, 0, 2),
            ("Phone / WhatsApp", self.phone, 0, 4), ("Item Name", self.item_name, 1, 0),
            ("Item Type", self.item_type, 1, 2), ("Brand", self.brand, 1, 4),
            ("Model", self.model, 2, 0), ("Serial No.", self.serial, 2, 2),
            ("Received Date", self.received_date, 2, 4), ("Expected Date", self.expected_date, 3, 0),
        ]
        for label, widget, r, c in fields:
            eg.addWidget(QLabel(label + ":"), r, c); eg.addWidget(widget, r, c + 1)
        eg.addWidget(QLabel("Condition When Received:"), 4, 0); eg.addWidget(self.condition, 4, 1, 1, 5)
        eg.addWidget(QLabel("Reported Problem:"), 5, 0); eg.addWidget(self.problem, 5, 1, 1, 5)
        eg.addWidget(QLabel("Fault / Defective Parts:"), 6, 0); eg.addWidget(self.fault, 6, 1, 1, 5)
        eg.addWidget(QLabel("Technician Notes:"), 7, 0); eg.addWidget(self.technician, 7, 1, 1, 5)


        estimate_group = QGroupBox("Repair Estimate / Requirements")
        ev = QVBoxLayout(estimate_group)
        ev.setContentsMargins(12, 14, 12, 12)
        ev.setSpacing(10)

        self.items_table = QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels([
            "Requirement / Product", "Qty", "Unit Cost", "Expense", "Remove"
        ])
        self.items_table.setMinimumHeight(145)
        self.items_table.setMaximumHeight(16777215)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setWordWrap(False)
        self.items_table.setTextElideMode(Qt.ElideRight)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SingleSelection)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(True)
        self.items_table.verticalHeader().setDefaultSectionSize(36)
        self.items_table.horizontalHeader().setMinimumSectionSize(70)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setStretchLastSection(False)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.items_table.setColumnWidth(1, 65)

        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.items_table.setColumnWidth(2, 105)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.items_table.setColumnWidth(3, 115)
        self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.items_table.setColumnWidth(4, 105)
        ev.addWidget(self.items_table, 0)


        item_btns = QHBoxLayout()
        item_btns.setSpacing(8)
        add_req_btn = apply_professional_icon(QPushButton('Add Requirement'), 'fa5s.plus', '#FFFFFF')
        edit_req_btn = apply_professional_icon(QPushButton('Edit Selected'), 'fa5s.pen', '#FFFFFF')
        remove_req_btn = apply_professional_icon(QPushButton('Remove Selected'), 'fa5s.trash-alt', '#FFFFFF')
        for b, slot in [
            (add_req_btn, self.add_estimate_item),
            (edit_req_btn, self.edit_estimate_item),
            (remove_req_btn, self.remove_estimate_item),
        ]:
            b.setMinimumHeight(34)
            b.clicked.connect(slot)
            item_btns.addWidget(b)
        item_btns.addStretch(1)
        ev.addLayout(item_btns)
        charge_row = QHBoxLayout()
        self.labour = QDoubleSpinBox(); self.labour.setRange(0, 100000000); self.labour.setDecimals(2); self.labour.setPrefix("Rs. "); self.labour.valueChanged.connect(self.update_estimate_total)
        self.other = QDoubleSpinBox(); self.other.setRange(0, 100000000); self.other.setDecimals(2); self.other.setPrefix("Rs. "); self.other.valueChanged.connect(self.update_estimate_total)
        self.discount = QDoubleSpinBox(); self.discount.setRange(0, 100000000); self.discount.setDecimals(2); self.discount.setPrefix("Rs. "); self.discount.valueChanged.connect(self.update_estimate_total)
        for label, w in [("Labour", self.labour), ("Other Charges", self.other), ("Discount", self.discount)]: charge_row.addWidget(QLabel(label + ":")); charge_row.addWidget(w)
        charge_row.addStretch(); ev.addLayout(charge_row)
        self.estimate_total = QLabel("Estimated Total: Rs. 0.00")
        self.estimate_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        ev.addWidget(self.estimate_total)
        eg.addWidget(estimate_group, 8, 0, 1, 6)
        eg.setRowMinimumHeight(8, 330)

        self.status = QComboBox(); self.status.addItems(["Pending Approval", "Approved", "Rejected", "In Repair", "Ready for Delivery", "Delivered", "Cancelled"])
        eg.addWidget(QLabel("Status:"), 9, 0); eg.addWidget(self.status, 9, 1)
        self.save_btn = apply_professional_icon(QPushButton('Save Repair / Estimate'), 'fa5s.save', '#FFFFFF'); self.save_btn.clicked.connect(self.save_repair)
        self.pdf_btn = apply_professional_icon(QPushButton('Generate Raw Bill PDF'), 'fa5s.file-pdf', '#FFFFFF'); self.pdf_btn.clicked.connect(self.generate_estimate_pdf)
        self.approve_btn = apply_professional_icon(QPushButton('Approve Estimate'), 'fa5s.check-circle', '#FFFFFF'); self.approve_btn.clicked.connect(lambda: self.set_status("Approved"))
        self.reject_btn = apply_professional_icon(QPushButton('Reject Estimate'), 'fa5s.times-circle', '#FFFFFF'); self.reject_btn.clicked.connect(lambda: self.set_status("Rejected"))
        self.actual_btn = apply_professional_icon(QPushButton('Create Actual Bill'), 'fa5s.file-invoice', '#FFFFFF'); self.actual_btn.clicked.connect(self.create_actual_bill)
        self.open_actual_btn = apply_professional_icon(QPushButton('Open Actual Bill'), 'fa5s.folder-open', '#FFFFFF'); self.open_actual_btn.clicked.connect(self.open_actual_bill)
        self.save_actual_btn = apply_professional_icon(QPushButton('Save Actual Bill As...'), 'fa5s.save', '#FFFFFF'); self.save_actual_btn.clicked.connect(self.save_actual_bill_as)

        action_buttons = [
            self.save_btn, self.pdf_btn, self.approve_btn,
            self.reject_btn, self.actual_btn, self.open_actual_btn
        ]
        for col, button in enumerate(action_buttons):
            eg.addWidget(button, 10, col)
        eg.addWidget(self.save_actual_btn, 11, 0, 1, 6)


        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.editor.setMinimumHeight(0)
        scroll.setWidget(self.editor)
        outer.addWidget(scroll, 1)

    def new_repair(self):
        self.current_id = None; self.estimate_items = []; self.last_actual_pdf_path = None
        self.repair_no.setText("New Repair Job")
        for w in [self.customer, self.phone, self.item_name, self.item_type, self.brand, self.model, self.serial]: w.clear()
        for w in [self.condition, self.problem, self.fault, self.technician]: w.clear()
        self.received_date.setDate(QDate.currentDate()); self.expected_date.setDate(QDate.currentDate().addDays(2))
        self.labour.setValue(0); self.other.setValue(0); self.discount.setValue(0); self.status.setCurrentText("Pending Approval")
        self.refresh_items(); self.update_buttons()

    def refresh_jobs(self):
        try:
            rows = self.db.get_repair_jobs(self.search.text().strip())
            self.jobs_table.setRowCount(0)
            for row in rows:
                r = self.jobs_table.rowCount(); self.jobs_table.insertRow(r)
                values = [row['repair_number'], row['customer_name'], row['item_name'], row['received_date'], f"Rs. {float(row['estimate_total'] or 0):,.2f}", row['status'], row['actual_bill_number'] or "-", "Open"]
                for c, value in enumerate(values): self.jobs_table.setItem(r, c, QTableWidgetItem(str(value)))
                b = apply_professional_icon(QPushButton('Open'), 'fa5s.folder-open', '#FFFFFF'); b.clicked.connect(lambda _, rid=row['id']: self.load_repair(rid)); self.jobs_table.setCellWidget(r, 7, b)
        except Exception as e:
            QMessageBox.critical(self, "Repair Error", str(e))

    def open_selected(self, row, col):
        item = self.jobs_table.item(row, 0)
        if item:
            found = self.db.find_repair_by_number(item.text())
            if found: self.load_repair(found['id'])

    def load_repair(self, repair_id):
        row = self.db.get_repair_job(repair_id)
        if not row: return
        self.current_id = repair_id; self.repair_no.setText(row['repair_number'])
        self.customer.setText(row['customer_name'] or ''); self.phone.setText(row['customer_phone'] or '')
        self.item_name.setText(row['item_name'] or ''); self.item_type.setText(row['item_type'] or '')
        self.brand.setText(row['brand'] or ''); self.model.setText(row['model'] or ''); self.serial.setText(row['serial_number'] or '')
        received_qdate = QDate.fromString(row['received_date'] or '', 'yyyy-MM-dd')
        expected_qdate = QDate.fromString(row['expected_date'] or '', 'yyyy-MM-dd')
        self.received_date.setDate(received_qdate if received_qdate.isValid() else QDate.currentDate())
        self.expected_date.setDate(expected_qdate if expected_qdate.isValid() else QDate.currentDate().addDays(2))
        self.condition.setPlainText(row['condition_received'] or ''); self.problem.setPlainText(row['reported_problem'] or '')
        self.fault.setPlainText(row['fault_details'] or ''); self.technician.setPlainText(row['technician_notes'] or '')
        self.estimate_items = [dict(x) for x in self.db.get_repair_estimate_items(repair_id)]
        est = self.db.get_repair_estimate(repair_id)
        self.labour.setValue(float(est['labour_amount'] or 0) if est else 0); self.other.setValue(float(est['other_charges'] or 0) if est else 0); self.discount.setValue(float(est['discount'] or 0) if est else 0)
        self.status.setCurrentText(row['status'] or 'Pending Approval')
        actual = self.db.get_repair_actual(repair_id)
        if actual:
            candidate = os.path.join(os.getcwd(), "repair_bills", f"{actual['bill_number']}.pdf")
            self.last_actual_pdf_path = candidate if os.path.exists(candidate) else None
        else:
            self.last_actual_pdf_path = None
        self.refresh_items(); self.update_buttons()

    def collect_job(self):
        if not self.customer.text().strip() or not self.item_name.text().strip():
            raise ValueError("Customer Name and Item Name are required.")
        return dict(customer_name=self.customer.text().strip(), customer_phone=self.phone.text().strip(), item_name=self.item_name.text().strip(), item_type=self.item_type.text().strip(), brand=self.brand.text().strip(), model=self.model.text().strip(), serial_number=self.serial.text().strip(), received_date=self.received_date.date().toString('yyyy-MM-dd'), expected_date=self.expected_date.date().toString('yyyy-MM-dd'), condition_received=self.condition.toPlainText().strip(), reported_problem=self.problem.toPlainText().strip(), fault_details=self.fault.toPlainText().strip(), accessories="", technician_notes=self.technician.toPlainText().strip(), status=self.status.currentText())

    def save_repair(self):
        try:
            data = self.collect_job()
            if self.current_id:
                self.db.update_repair_job(self.current_id, data)
                rid = self.current_id
            else:
                rid = self.db.create_repair_job(data); self.current_id = rid
            self.db.save_repair_estimate(rid, self.estimate_items, self.labour.value(), self.other.value(), self.discount.value())
            row = self.db.get_repair_job(rid); self.repair_no.setText(row['repair_number'])
            self.refresh_jobs(); self.update_buttons()
            QMessageBox.information(self, "Saved", f"Repair job {row['repair_number']} saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def ensure_saved(self):
        if not self.current_id:
            self.save_repair()
        return bool(self.current_id)

    def refresh_items(self):
        self.items_table.setRowCount(0)
        for i, item in enumerate(self.estimate_items):
            r = self.items_table.rowCount()
            self.items_table.insertRow(r)
            total = float(item['quantity']) * float(item['unit_cost'])

            description = QTableWidgetItem(str(item.get('description', '')))
            description.setToolTip(str(item.get('description', '')))
            description.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.items_table.setItem(r, 0, description)
            self.items_table.setItem(r, 1, QTableWidgetItem(str(item.get('quantity', 1))))
            self.items_table.setItem(r, 2, QTableWidgetItem(f"Rs. {float(item.get('unit_cost', 0)):,.2f}"))
            self.items_table.setItem(r, 3, QTableWidgetItem(f"Rs. {total:,.2f}"))

            remove_btn = apply_professional_icon(QPushButton('Remove'), 'fa5s.trash-alt', '#FFFFFF')
            remove_btn.setMinimumHeight(30)
            remove_btn.clicked.connect(lambda _, rr=i: self.remove_estimate_index(rr))
            self.items_table.setCellWidget(r, 4, remove_btn)
            self.items_table.setRowHeight(r, 36)

        self.update_estimate_total()

    def add_estimate_item(self):
        dlg = RepairItemDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.estimate_items.append(dlg.values()); self.refresh_items()

    def edit_estimate_item(self):
        r = self.items_table.currentRow()
        if r < 0 or r >= len(self.estimate_items): return
        dlg = RepairItemDialog(self, self.estimate_items[r], "Edit Requirement")
        if dlg.exec() == QDialog.Accepted: self.estimate_items[r] = dlg.values(); self.refresh_items()

    def remove_estimate_item(self):
        r = self.items_table.currentRow(); self.remove_estimate_index(r)

    def remove_estimate_index(self, r):
        if 0 <= r < len(self.estimate_items): self.estimate_items.pop(r); self.refresh_items()

    def update_estimate_total(self):
        materials = sum(float(x['quantity']) * float(x['unit_cost']) for x in self.estimate_items)
        total = max(0, materials + self.labour.value() + self.other.value() - self.discount.value())
        self.estimate_total.setText(f"Estimated Total: Rs. {total:,.2f}")

    def set_status(self, status):
        if not self.ensure_saved(): return
        try:
            self.db.set_repair_status(self.current_id, status)
            self.status.setCurrentText(status); self.refresh_jobs(); self.update_buttons()
        except Exception as e: QMessageBox.critical(self, "Status Error", str(e))

    def update_buttons(self):
        exists = bool(self.current_id)
        approved = self.status.currentText() in ("Approved", "In Repair", "Ready for Delivery", "Delivered")
        self.pdf_btn.setEnabled(exists); self.approve_btn.setEnabled(exists); self.reject_btn.setEnabled(exists)
        self.actual_btn.setEnabled(exists and approved)
        has_actual_pdf = bool(self.last_actual_pdf_path and os.path.exists(self.last_actual_pdf_path))
        self.open_actual_btn.setEnabled(has_actual_pdf)
        self.save_actual_btn.setEnabled(has_actual_pdf)

    def build_pdf(self, actual=False):
        """
        Generate the repair PDF using the same professional layout as the
        actual repair bill.

        Raw/estimate PDF:
            - Same shop header
            - Same customer/item information table
            - Same condition/problem/fault/technician table
            - Same requirement/product table
            - Same charges/total section
            - Same terms & conditions second page

        Actual PDF:
            This method is retained for the manual "Generate PDF" action.
            The automatically-created actual bill continues to use
            build_actual_pdf_without_prompt().
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table,
                TableStyle, PageBreak
            )
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
        except ImportError:
            raise RuntimeError(
                "PDF generation requires reportlab. Install it with: "
                "pip install reportlab"
            )

        row = self.db.get_repair_job(self.current_id)
        if not row:
            raise RuntimeError("Repair job not found.")

        est = self.db.get_repair_estimate(self.current_id)
        if not est:
            raise RuntimeError("Repair estimate not found.")

        items = self.db.get_repair_estimate_items(self.current_id)

        bill = None
        if actual:
            bill = self.db.get_repair_actual(self.current_id)
            if not bill:
                raise RuntimeError("Actual bill not found.")
            items = self.db.get_repair_actual_items(self.current_id)

        default_name = (
            f"{row['repair_number']}_"
            f"{'ActualBill' if actual else 'RepairEstimate'}.pdf"
        )

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Repair PDF",
            os.path.join(os.getcwd(), default_name),
            "PDF Files (*.pdf)"
        )
        if not path:
            return None

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=32,
            leftMargin=32,
            topMargin=30,
            bottomMargin=30,
            title=(
                f"{'Actual Repair Bill' if actual else 'Repair Estimate'} - "
                f"{row['repair_number']}"
            ),
            author=SHOP_DEFAULT
        )

        styles = getSampleStyleSheet()
        purple = colors.HexColor("#51408A")
        light_purple = colors.HexColor("#F2EFFA")
        dark = colors.HexColor("#202040")

        title_style = ParagraphStyle(
            "RawShopTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=24,
            alignment=TA_CENTER,
            textColor=purple,
            spaceAfter=5
        )

        subtitle_style = ParagraphStyle(
            "RawShopSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=dark
        )

        bill_title = ParagraphStyle(
            "RawBillTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=purple,
            spaceBefore=8,
            spaceAfter=8
        )

        small = ParagraphStyle(
            "RawSmall",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11
        )

        small_bold = ParagraphStyle(
            "RawSmallBold",
            parent=small,
            fontName="Helvetica-Bold"
        )

        term_style = ParagraphStyle(
            "RawTerm",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            spaceAfter=7
        )

        def P(value, style=small):
            """Safely render dynamic text without exposing HTML tags."""
            if value is None or str(value).strip() == "":
                value = "-"
            return Paragraph(html.escape(str(value)), style)

        def B(label):
            """Render a bold label without putting literal <b> tags in PDF."""
            return Paragraph(html.escape(str(label)), small_bold)

        def shop_header():
            info = Table(
                [[
                    P(SHOP_DEALS, subtitle_style),
                    P(SHOP_PHONE, subtitle_style)
                ]],
                colWidths=[360, 160]
            )
            info.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1.5, purple),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, purple),
                ("BACKGROUND", (0, 0), (-1, -1), light_purple),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))

            address = Table(
                [[P(SHOP_ADDRESS, subtitle_style)]],
                colWidths=[520]
            )
            address.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), purple),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, purple),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))

            return [
                Paragraph(SHOP_DEFAULT, title_style),
                info,
                Spacer(1, 3),
                address
            ]

        story = []
        story.extend(shop_header())
        story.append(
            Paragraph(
                "ACTUAL REPAIR BILL" if actual else "REPAIR ESTIMATE / RAW BILL",
                bill_title
            )
        )
        
        info_rows = [
            [
                B("Repair No."),
                P(row["repair_number"]),
                B("Bill No."),
                P(bill["bill_number"] if actual else "-")
            ],
            [
                B("Customer"),
                P(row["customer_name"]),
                B("Phone"),
                P(row["customer_phone"])
            ],
            [
                B("Item"),
                P(row["item_name"]),
                B("Brand / Model"),
                P(
                    f"{row['brand'] or '-'} / "
                    f"{row['model'] or '-'}"
                )
            ],
            [
                B("Serial No."),
                P(row["serial_number"]),
                B("Received"),
                P(row["received_date"])
            ],
            [
                B("Status"),
                P(row["status"]),
                B("Expected"),
                P(row["expected_date"])
            ],
        ]

        info_table = Table(
            info_rows,
            colWidths=[72, 190, 82, 176]
        )
        info_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), light_purple),
            ("BACKGROUND", (2, 0), (2, -1), light_purple),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([info_table, Spacer(1, 8)])
        
        details = [
            [B("Condition When Received"), P(row["condition_received"])],
            [B("Reported Problem"), P(row["reported_problem"])],
            [B("Fault / Defective Parts"), P(row["fault_details"])],
            [B("Technician Notes"), P(row["technician_notes"])],
        ]

        details_table = Table(
            details,
            colWidths=[145, 375]
        )
        details_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), light_purple),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([details_table, Spacer(1, 10)])


        data = [[
            B("Requirement / Product"),
            B("Qty"),
            B("Unit Cost"),
            B("Total")
        ]]

        for item in items:
            qty = float(item["quantity"])
            unit = float(item["unit_cost"])
            data.append([
                P(item["description"]),
                P(item["quantity"]),
                P(f"Rs. {unit:,.2f}"),
                P(f"Rs. {qty * unit:,.2f}")
            ])

        if len(data) == 1:
            data.append([
                P("No material / product"),
                P(""),
                P(""),
                P("Rs. 0.00")
            ])

        items_table = Table(
            data,
            repeatRows=1,
            colWidths=[260, 55, 95, 110]
        )
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), purple),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([items_table, Spacer(1, 10)])

        materials = sum(
            float(x["quantity"]) * float(x["unit_cost"])
            for x in items
        )

        if actual:
            labour = float(bill["labour_amount"] or 0)
            other = float(bill["other_charges"] or 0)
            discount = float(bill["discount"] or 0)
            total = float(bill["total_amount"] or 0)
            payment = str(bill["payment_method"] or "-")
            received = float(bill["amount_received"] or 0)
            balance = max(0, total - received)
        else:
            labour = float(est["labour_amount"] or 0)
            other = float(est["other_charges"] or 0)
            discount = float(est["discount"] or 0)
            total = float(est["total_amount"] or 0)
            payment = "Pending Approval"
            received = 0.0
            balance = total


        summary = [
            ["Materials", f"Rs. {materials:,.2f}"],
            ["Labour", f"Rs. {labour:,.2f}"],
            ["Other Charges", f"Rs. {other:,.2f}"],
            ["Discount", f"Rs. {discount:,.2f}"],
            ["TOTAL", f"Rs. {total:,.2f}"],
            ["Payment", payment],
            [
                "Amount Received",
                "-" if not actual else f"Rs. {received:,.2f}"
            ],
            [
                "Balance",
                "-" if not actual else f"Rs. {balance:,.2f}"
            ],
        ]

        summary_table = Table(
            summary,
            colWidths=[155, 145],
            hAlign="RIGHT"
        )
        summary_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
            ("BACKGROUND", (0, 4), (-1, 4), light_purple),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(summary_table)

        if actual and bill["notes"]:
            story.append(Spacer(1, 8))
            notes_table = Table(
                [[B("Notes:"), P(bill["notes"])]],
                colWidths=[55, 465]
            )
            notes_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(notes_table)

        story.append(Spacer(1, 10))
        story.append(
            P(
                "Note: This is a repair estimate/raw bill and is subject "
                "to customer approval."
                if not actual
                else "Thank you. Please retain this bill for repair/service reference."
            )
        )


        story.append(PageBreak())
        story.append(
            Paragraph("REPAIRING TERMS & CONDITIONS", bill_title)
        )
        story.append(Spacer(1, 4))

        for number, term in enumerate(REPAIRING_TERMS, start=1):
            story.append(
                Paragraph(
                    f"<b>{number}.</b> {html.escape(term)}",
                    term_style
                )
            )

        story.append(Spacer(1, 12))

        footer_left = f"Repair No: {row['repair_number']}"
        footer_right = (
            f"Bill No: {bill['bill_number']}"
            if actual
            else "Bill No: -"
        )

        footer = Table([[
            B(footer_left),
            B(footer_right)
        ]], colWidths=[260, 260])

        footer.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, purple),
            ("BACKGROUND", (0, 0), (-1, -1), light_purple),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(footer)

        doc.build(story)
        return path

    def generate_estimate_pdf(self):
        if not self.ensure_saved(): return
        try:
            path = self.build_pdf(False)
            if path: QMessageBox.information(self, "PDF Ready", f"Repair estimate saved:\n\n{path}")
        except Exception as e: QMessageBox.critical(self, "PDF Error", str(e))

    def create_actual_bill(self):
        if not self.ensure_saved():
            return

        if self.status.currentText() not in ("Approved", "In Repair", "Ready for Delivery", "Delivered"):
            QMessageBox.warning(
                self,
                "Approval Required",
                "Customer must approve the estimate before an actual bill can be created."
            )
            return

        try:
            
            existing = self.db.get_repair_actual(self.current_id)
            if existing:
                self.last_actual_pdf_path = os.path.join(
                    os.getcwd(), "repair_bills", f"{existing['bill_number']}.pdf"
                )
                if os.path.exists(self.last_actual_pdf_path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_actual_pdf_path))
                    QMessageBox.information(
                        self,
                        "Actual Bill Already Exists",
                        f"Actual bill {existing['bill_number']} already exists.\n\n"
                        "The existing PDF has been opened."
                    )
                else:
                    self.last_actual_pdf_path = self.build_actual_pdf_without_prompt(existing["id"])
                    if self.last_actual_pdf_path:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_actual_pdf_path))
                self.update_buttons()
                return

            repair = self.db.get_repair_job(self.current_id)
            items = self.db.get_repair_estimate_items(self.current_id)
            if not repair:
                raise RuntimeError("Repair job not found.")

            dlg = ActualBillDialog(self, repair, items)
            if dlg.exec() != QDialog.Accepted:
                return

            values = dlg.values()
            bill_id = self.db.create_repair_actual_bill(self.current_id, values)
            self.db.set_repair_status(self.current_id, "Ready for Delivery")

            path = self.build_actual_pdf_without_prompt(bill_id)
            self.last_actual_pdf_path = path

            self.refresh_jobs()
            self.load_repair(self.current_id)

            if path:
                self.last_actual_pdf_path = path
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

            actual = self.db.get_repair_actual(self.current_id)
            msg = f"Actual bill created successfully.\n\nBill No: {actual['bill_number']}"
            if path:
                msg += f"\nPDF: {path}"
            QMessageBox.information(self, "Actual Bill Created", msg)

        except Exception as e:
            QMessageBox.critical(self, "Actual Bill Error", str(e))

    def open_actual_bill(self):
        """Open the generated actual repair bill PDF in the system PDF viewer."""
        if not self.last_actual_pdf_path or not os.path.exists(self.last_actual_pdf_path):
            QMessageBox.information(
                self, "Actual Bill",
                "No generated actual bill PDF was found. Create the actual bill first."
            )
            self.update_buttons()
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_actual_pdf_path))

    def save_actual_bill_as(self):
        """Copy the generated actual bill to a location selected by the user."""
        if not self.last_actual_pdf_path or not os.path.exists(self.last_actual_pdf_path):
            QMessageBox.information(
                self, "Actual Bill",
                "No generated actual bill PDF was found. Create the actual bill first."
            )
            self.update_buttons()
            return

        default_name = os.path.basename(self.last_actual_pdf_path)
        target, _ = QFileDialog.getSaveFileName(
            self, "Save Actual Repair Bill", default_name, "PDF Files (*.pdf)"
        )
        if not target:
            return
        if not target.lower().endswith(".pdf"):
            target += ".pdf"

        try:
            shutil.copy2(self.last_actual_pdf_path, target)
            QMessageBox.information(
                self, "Saved", f"Actual bill saved successfully:\n\n{target}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def build_actual_pdf_without_prompt(self, bill_id):
        """Create the actual repair bill. Page 2 is the reverse-side terms page."""
        row = self.db.get_repair_job(self.current_id)
        bill = self.db.get_repair_actual(self.current_id)
        items = self.db.get_repair_actual_items(self.current_id)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
        except ImportError:
            return None

        folder = os.path.join(os.getcwd(), "repair_bills")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{bill['bill_number']}.pdf")

        doc = SimpleDocTemplate(
            path, pagesize=A4,
            rightMargin=32, leftMargin=32, topMargin=30, bottomMargin=30,
            title=f"Actual Repair Bill - {bill['bill_number']}",
            author=SHOP_DEFAULT
        )

        styles = getSampleStyleSheet()
        purple = colors.HexColor("#51408A")
        light_purple = colors.HexColor("#F2EFFA")
        dark = colors.HexColor("#202040")

        title_style = ParagraphStyle(
            "ShopTitle", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=21, leading=24, alignment=TA_CENTER, textColor=purple,
            spaceAfter=5
        )
        subtitle_style = ParagraphStyle(
            "ShopSubtitle", parent=styles["Normal"], fontName="Helvetica",
            fontSize=9, leading=11, alignment=TA_CENTER, textColor=dark
        )
        bill_title = ParagraphStyle(
            "BillTitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=15, leading=18, alignment=TA_CENTER, textColor=purple,
            spaceBefore=8, spaceAfter=8
        )
        small = ParagraphStyle(
            "Small", parent=styles["Normal"], fontSize=8.5, leading=11
        )
        term_style = ParagraphStyle(
            "Term", parent=styles["Normal"], fontSize=9.5, leading=14, spaceAfter=7
        )

        def P(value, style=small):
            if value is None or str(value).strip() == "":
                value = "-"
            return Paragraph(html.escape(str(value)), style)

        small_bold = ParagraphStyle(
            "ActualSmallBold",
            parent=small,
            fontName="Helvetica-Bold"
        )

        def B(label):
            return Paragraph(html.escape(str(label)), small_bold)

        def shop_header():
 
 
            info = Table(
                [[P(SHOP_DEALS, subtitle_style), P(SHOP_PHONE, subtitle_style)]],
                colWidths=[360, 160]
            )
            info.setStyle(TableStyle([
                ("BOX", (0,0), (-1,-1), 1.5, purple),
                ("INNERGRID", (0,0), (-1,-1), 0.5, purple),
                ("BACKGROUND", (0,0), (-1,-1), light_purple),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("LEFTPADDING", (0,0), (-1,-1), 8),
                ("RIGHTPADDING", (0,0), (-1,-1), 8),
                ("TOPPADDING", (0,0), (-1,-1), 7),
                ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ]))

            address = Table([[P(SHOP_ADDRESS, subtitle_style)]], colWidths=[520])
            address.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), purple),
                ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
                ("BOX", (0,0), (-1,-1), 1, purple),
                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            return [Paragraph(SHOP_DEFAULT, title_style), info, Spacer(1,3), address]

        story = []
        story.extend(shop_header())
        story.append(Paragraph("ACTUAL REPAIR BILL", bill_title))

        info = [
            [B("Repair No."), P(row["repair_number"]), B("Bill No."), P(bill["bill_number"])],
            [B("Customer"), P(row["customer_name"]), B("Phone"), P(row["customer_phone"])],
            [B("Item"), P(row["item_name"]), B("Brand / Model"), P(f"{row['brand'] or '-'} / {row['model'] or '-'}")],
            [B("Serial No."), P(row["serial_number"]), B("Received"), P(row["received_date"])],
            [B("Status"), P(row["status"]), B("Expected"), P(row["expected_date"])],
        ]
        info_table = Table(info, colWidths=[72,190,82,176])
        info_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (0,-1), light_purple),
            ("BACKGROUND", (2,0), (2,-1), light_purple),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.extend([info_table, Spacer(1,8)])

        details = [
            [B("Condition When Received"), P(row["condition_received"])],
            [B("Reported Problem"), P(row["reported_problem"])],
            [B("Fault / Defective Parts"), P(row["fault_details"])],
            [B("Technician Notes"), P(row["technician_notes"])],
        ]
        details_table = Table(details, colWidths=[145,375])
        details_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (0,-1), light_purple),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.extend([details_table, Spacer(1,10)])

        data = [[
            B("Requirement / Product"), B("Qty"),
            B("Unit Cost"), B("Total")
        ]]
        for x in items:
            qty = float(x["quantity"])
            unit = float(x["unit_cost"])
            data.append([
                P(x["description"]), P(str(x["quantity"])),
                P(f"Rs. {unit:,.2f}"), P(f"Rs. {qty * unit:,.2f}")
            ])

        if len(data) == 1:
            data.append([P("No material / product"), P(""), P(""), P("Rs. 0.00")])

        items_table = Table(data, repeatRows=1, colWidths=[260,55,95,110])
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), purple),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (1,1), (-1,-1), "RIGHT"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.extend([items_table, Spacer(1,10)])

        materials = sum(float(x["quantity"]) * float(x["unit_cost"]) for x in items)
        total = float(bill["total_amount"] or 0)
        received = float(bill["amount_received"] or 0)
        balance = max(0, total - received)

        summary = [
            ["Materials", f"Rs. {materials:,.2f}"],
            ["Labour", f"Rs. {float(bill['labour_amount'] or 0):,.2f}"],
            ["Other Charges", f"Rs. {float(bill['other_charges'] or 0):,.2f}"],
            ["Discount", f"Rs. {float(bill['discount'] or 0):,.2f}"],
            ["TOTAL", f"Rs. {total:,.2f}"],
            ["Payment", str(bill["payment_method"] or "-")],
            ["Amount Received", f"Rs. {received:,.2f}"],
            ["Balance", f"Rs. {balance:,.2f}"],
        ]
        summary_table = Table(summary, colWidths=[155,145], hAlign="RIGHT")
        summary_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,4), (-1,4), "Helvetica-Bold"),
            ("BACKGROUND", (0,4), (-1,4), light_purple),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("LEFTPADDING", (0,0), (-1,-1), 7),
            ("RIGHTPADDING", (0,0), (-1,-1), 7),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(summary_table)

        if bill["notes"]:
            story.append(Spacer(1, 8))
            notes_table = Table(
                [[B("Notes:"), P(bill["notes"])]],
                colWidths=[55, 465]
            )
            notes_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(notes_table)

        story.append(Spacer(1,10))
        story.append(P("Thank you. Please retain this bill for repair/service reference.", small))


        story.append(PageBreak())
        story.append(Paragraph("REPAIRING TERMS & CONDITIONS", bill_title))
        story.append(Spacer(1,4))

        for number, term in enumerate(REPAIRING_TERMS, start=1):
            story.append(Paragraph(f"<b>{number}.</b> {term}", term_style))

        story.append(Spacer(1,12))
        footer = Table([[
            B(f"Repair No: {row['repair_number']}"),
            B(f"Bill No: {bill['bill_number']}")
        ]], colWidths=[260, 260])
        footer.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 0.8, purple),
            ("BACKGROUND", (0,0), (-1,-1), light_purple),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(footer)

        doc.build(story)
        return path

