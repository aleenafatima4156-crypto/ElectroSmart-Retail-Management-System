import sqlite3
import os
from collections import defaultdict


class DatabaseManager:
    """
    SQLite database layer for ElectroSmart.

    Active modules:
      - Products
      - POS / Sales
      - Sales History
      - Reports

    Customer/Khaata and Purchase/Supplier modules are intentionally not part
    of this database layer anymore. Customer name/phone are kept as simple
    invoice fields so POS can still print customer information without a
    customer master table.
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "database", "electrosmart.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_tables()



    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _validate_cart(cart_items):
        if not cart_items:
            raise ValueError("Sale must contain at least one product.")

        normalized = []
        totals = defaultdict(int)

        for item in cart_items:
            try:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
                price = float(item["price"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Invalid cart item data.") from exc

            name = str(item.get("name", "")).strip() or f"Product #{product_id}"

            if product_id <= 0:
                raise ValueError(f"Invalid product ID for '{name}'.")
            if quantity <= 0:
                raise ValueError(f"Invalid quantity for '{name}'.")
            if price < 0:
                raise ValueError(f"Invalid selling price for '{name}'.")

            normalized.append({
                "product_id": product_id,
                "name": name,
                "quantity": quantity,
                "price": price,
            })
            totals[product_id] += quantity

        return normalized, totals

    @staticmethod
    def _add_column_if_missing(cursor, table_name, column_name, definition):
        columns = {
            row["name"]
            for row in cursor.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
        }
        if column_name not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
            )



    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    brand TEXT,
                    purchase_price REAL DEFAULT 0,
                    selling_price REAL NOT NULL,
                    stock INTEGER DEFAULT 0,
                    min_stock INTEGER DEFAULT 0,
                    unit TEXT DEFAULT 'Piece',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    total_amount REAL DEFAULT 0,
                    payment_method TEXT DEFAULT 'Cash',
                    customer_name TEXT DEFAULT '',
                    customer_phone TEXT DEFAULT '',
                    discount REAL DEFAULT 0,
                    labour_amount REAL DEFAULT 0,
                    cash_received REAL DEFAULT 0,
                    paper_size TEXT DEFAULT 'A4',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    cost_price REAL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)


            self._add_column_if_missing(cursor, "sales", "customer_phone",
                                        "TEXT DEFAULT ''")
            self._add_column_if_missing(cursor, "sales", "discount",
                                        "REAL DEFAULT 0")
            self._add_column_if_missing(cursor, "sales", "labour_amount",
                                        "REAL DEFAULT 0")
            self._add_column_if_missing(cursor, "sales", "cash_received",
                                        "REAL DEFAULT 0")
            self._add_column_if_missing(cursor, "sales", "paper_size",
                                        "TEXT DEFAULT 'A4'")


            
            self._add_column_if_missing(cursor, "sale_items", "cost_price",
                                        "REAL")

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sales_created_at
                ON sales(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id
                ON sale_items(sale_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sale_items_product_id
                ON sale_items(product_id)
            """)

            self.create_repair_tables(cursor)

            conn.commit()

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()



    def add_product(
        self,
        name,
        category="",
        brand="",
        purchase_price=0,
        selling_price=0,
        stock=0,
        min_stock=0,
        unit="Piece",
    ):
        name = str(name).strip()
        if not name:
            raise ValueError("Product name is required.")

        purchase_price = float(purchase_price)
        selling_price = float(selling_price)
        stock = int(stock)
        min_stock = int(min_stock)

        if purchase_price < 0:
            raise ValueError("Purchase price cannot be negative.")
        if selling_price < 0:
            raise ValueError("Selling price cannot be negative.")
        if stock < 0:
            raise ValueError("Stock cannot be negative.")
        if min_stock < 0:
            raise ValueError("Minimum stock cannot be negative.")

        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (
                    name, category, brand, purchase_price,
                    selling_price, stock, min_stock, unit
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, str(category).strip(), str(brand).strip(),
                purchase_price, selling_price, stock, min_stock,
                str(unit).strip() or "Piece",
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_products(self):
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    id, name, category, brand, purchase_price,
                    selling_price, stock, min_stock, unit, created_at
                FROM products
                ORDER BY id DESC
            """).fetchall()
        finally:
            conn.close()

    def get_product(self, product_id):
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    id, name, category, brand, purchase_price,
                    selling_price, stock, min_stock, unit, created_at
                FROM products
                WHERE id = ?
            """, (int(product_id),)).fetchone()
        finally:
            conn.close()

    def update_product_stock(self, product_id, new_stock):
        new_stock = int(new_stock)
        if new_stock < 0:
            raise ValueError("Stock cannot be negative.")

        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products
                SET stock = ?
                WHERE id = ?
            """, (new_stock, int(product_id)))

            if cursor.rowcount == 0:
                raise ValueError("Product not found.")

            conn.commit()
        finally:
            conn.close()



    def get_next_invoice_number(self):
        conn = self.connect()
        try:
            row = conn.execute("""
                SELECT id
                FROM sales
                ORDER BY id DESC
                LIMIT 1
            """).fetchone()

            next_number = (row["id"] + 1) if row else 1
            return f"INV-{next_number:05d}"
        finally:
            conn.close()

    def create_sale(
        self,
        invoice_number,
        cart_items,
        total_amount,
        payment_method="Cash",
        customer_name="",
        customer_phone="",
        customer_id=None,     
        
        discount=0,
        labour_amount=0,
        cash_received=0,
        paper_size="A4",
    ):
        del customer_id 
        
        invoice_number = str(invoice_number).strip()
        if not invoice_number:
            raise ValueError("Invoice number is required.")

        items, totals = self._validate_cart(cart_items)
        total_amount = float(total_amount)
        discount = float(discount)
        labour_amount = float(labour_amount)
        cash_received = float(cash_received)

        if total_amount < 0:
            raise ValueError("Total amount cannot be negative.")
        if discount < 0:
            raise ValueError("Discount cannot be negative.")
        if labour_amount < 0:
            raise ValueError("Labour charges cannot be negative.")
        if cash_received < 0:
            raise ValueError("Cash received cannot be negative.")

        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")


            product_rows = {}
            for product_id, required_qty in totals.items():
                row = cursor.execute("""
                    SELECT id, name, stock, purchase_price
                    FROM products
                    WHERE id = ?
                """, (product_id,)).fetchone()

                if not row:
                    raise ValueError(f"Product ID {product_id} was not found.")

                if int(row["stock"]) < required_qty:
                    raise ValueError(
                        f"Insufficient stock for {row['name']}.\n"
                        f"Available: {row['stock']}\n"
                        f"Required: {required_qty}"
                    )

                product_rows[product_id] = row

            cursor.execute("""
                INSERT INTO sales (
                    invoice_number, total_amount, payment_method,
                    customer_name, customer_phone, discount,
                    labour_amount, cash_received, paper_size
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_number,
                total_amount,
                str(payment_method or "Cash").strip() or "Cash",
                str(customer_name or "").strip(),
                str(customer_phone or "").strip(),
                discount,
                labour_amount,
                cash_received,
                str(paper_size or "A4").strip() or "A4",
            ))

            sale_id = cursor.lastrowid

            for item in items:
                product = product_rows[item["product_id"]]
                cost_price = float(product["purchase_price"] or 0)
                subtotal = item["price"] * item["quantity"]

                cursor.execute("""
                    INSERT INTO sale_items (
                        sale_id, product_id, product_name,
                        quantity, price, cost_price, subtotal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sale_id,
                    item["product_id"],
                    item["name"],
                    item["quantity"],
                    item["price"],
                    cost_price,
                    subtotal,
                ))

            for product_id, quantity in totals.items():
                cursor.execute("""
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ? AND stock >= ?
                """, (quantity, product_id, quantity))

                if cursor.rowcount == 0:
                    raise ValueError("Stock changed while saving the sale. Please try again.")

            conn.commit()
            return sale_id

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update_sale(
        self,
        sale_id,
        cart_items,
        total_amount,
        payment_method="Cash",
        customer_name="",
        customer_phone="",
        customer_id=None,      
        discount=0,
        labour_amount=0,
        cash_received=0,
        paper_size=None,
    ):
        del customer_id

        items, totals = self._validate_cart(cart_items)
        total_amount = float(total_amount)
        discount = float(discount)
        labour_amount = float(labour_amount)
        cash_received = float(cash_received)

        if total_amount < 0:
            raise ValueError("Total amount cannot be negative.")
        if discount < 0:
            raise ValueError("Discount cannot be negative.")
        if labour_amount < 0:
            raise ValueError("Labour charges cannot be negative.")
        if cash_received < 0:
            raise ValueError("Cash received cannot be negative.")

        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN IMMEDIATE")

            old_sale = cursor.execute("""
                SELECT id, paper_size
                FROM sales
                WHERE id = ?
            """, (int(sale_id),)).fetchone()

            if not old_sale:
                raise ValueError("Sale not found.")

            old_items = cursor.execute("""
                SELECT product_id, product_name, quantity
                FROM sale_items
                WHERE sale_id = ?
            """, (int(sale_id),)).fetchall()

            for old in old_items:
                cursor.execute("""
                    UPDATE products
                    SET stock = stock + ?
                    WHERE id = ?
                """, (int(old["quantity"]), int(old["product_id"])))

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Product '{old['product_name']}' no longer exists."
                    )

            product_rows = {}
            for product_id, required_qty in totals.items():
                row = cursor.execute("""
                    SELECT id, name, stock, purchase_price
                    FROM products
                    WHERE id = ?
                """, (product_id,)).fetchone()

                if not row:
                    raise ValueError(f"Product ID {product_id} was not found.")

                if int(row["stock"]) < required_qty:
                    raise ValueError(
                        f"Insufficient stock for {row['name']}.\n"
                        f"Available: {row['stock']}\n"
                        f"Required: {required_qty}"
                    )

                product_rows[product_id] = row

            cursor.execute("""
                DELETE FROM sale_items
                WHERE sale_id = ?
            """, (int(sale_id),))

            for item in items:
                product = product_rows[item["product_id"]]
                cost_price = float(product["purchase_price"] or 0)
                subtotal = item["price"] * item["quantity"]

                cursor.execute("""
                    INSERT INTO sale_items (
                        sale_id, product_id, product_name,
                        quantity, price, cost_price, subtotal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(sale_id),
                    item["product_id"],
                    item["name"],
                    item["quantity"],
                    item["price"],
                    cost_price,
                    subtotal,
                ))

            for product_id, quantity in totals.items():
                cursor.execute("""
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ? AND stock >= ?
                """, (quantity, product_id, quantity))

                if cursor.rowcount == 0:
                    raise ValueError("Stock changed while updating the sale.")

            if paper_size is None:
                paper_size = old_sale["paper_size"] or "A4"

            cursor.execute("""
                UPDATE sales
                SET
                    total_amount = ?,
                    payment_method = ?,
                    customer_name = ?,
                    customer_phone = ?,
                    discount = ?,
                    labour_amount = ?,
                    cash_received = ?,
                    paper_size = ?
                WHERE id = ?
            """, (
                total_amount,
                str(payment_method or "Cash").strip() or "Cash",
                str(customer_name or "").strip(),
                str(customer_phone or "").strip(),
                discount,
                labour_amount,
                cash_received,
                str(paper_size or "A4").strip() or "A4",
                int(sale_id),
            ))

            if cursor.rowcount == 0:
                raise ValueError("Sale could not be updated.")

            conn.commit()
            return True

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_sales(self):
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    id, invoice_number, customer_name, customer_phone,
                    total_amount, payment_method, discount,
                    labour_amount, cash_received, paper_size, created_at
                FROM sales
                ORDER BY id DESC
            """).fetchall()
        finally:
            conn.close()

    def get_sale_by_id(self, sale_id):
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    id, invoice_number, customer_name, customer_phone,
                    total_amount, payment_method, discount,
                    labour_amount, cash_received, paper_size, created_at
                FROM sales
                WHERE id = ?
            """, (int(sale_id),)).fetchone()
        finally:
            conn.close()

    def get_sale_items(self, sale_id):
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    id, sale_id, product_id, product_name,
                    quantity, price, cost_price, subtotal
                FROM sale_items
                WHERE sale_id = ?
                ORDER BY id
            """, (int(sale_id),)).fetchall()
        finally:
            conn.close()



    def _repair_number(self):
        row = self.connect().execute("SELECT id FROM repair_jobs ORDER BY id DESC LIMIT 1").fetchone()
        next_id = (int(row["id"]) + 1) if row else 1
        return f"REP-{next_id:05d}"

    def create_repair_tables(self, cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_number TEXT UNIQUE NOT NULL,
                customer_name TEXT DEFAULT '',
                customer_phone TEXT DEFAULT '',
                item_name TEXT NOT NULL,
                item_type TEXT DEFAULT '', brand TEXT DEFAULT '', model TEXT DEFAULT '',
                serial_number TEXT DEFAULT '', received_date TEXT NOT NULL,
                expected_date TEXT DEFAULT '', condition_received TEXT DEFAULT '',
                reported_problem TEXT DEFAULT '', fault_details TEXT DEFAULT '',
                accessories TEXT DEFAULT '', technician_notes TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending Approval',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP, completed_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_id INTEGER UNIQUE NOT NULL,
                labour_amount REAL DEFAULT 0,
                other_charges REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(repair_id) REFERENCES repair_jobs(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_estimate_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL DEFAULT 1,
                unit_cost REAL DEFAULT 0,
                total REAL DEFAULT 0,
                FOREIGN KEY(repair_id) REFERENCES repair_jobs(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_actual_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_id INTEGER UNIQUE NOT NULL,
                bill_number TEXT UNIQUE NOT NULL,
                labour_amount REAL DEFAULT 0,
                other_charges REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'Cash',
                amount_received REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(repair_id) REFERENCES repair_jobs(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_actual_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL DEFAULT 1,
                unit_cost REAL DEFAULT 0,
                total REAL DEFAULT 0,
                FOREIGN KEY(repair_id) REFERENCES repair_jobs(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_repair_jobs_status ON repair_jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_repair_jobs_created_at ON repair_jobs(created_at)")

    def create_repair_job(self, data):
        conn = self.connect()
        try:
            cur = conn.cursor(); cur.execute("BEGIN IMMEDIATE")
            row = cur.execute("SELECT id FROM repair_jobs ORDER BY id DESC LIMIT 1").fetchone()
            num = f"REP-{((int(row['id']) + 1) if row else 1):05d}"
            cur.execute("""INSERT INTO repair_jobs
                (repair_number, customer_name, customer_phone, item_name, item_type, brand, model,
                 serial_number, received_date, expected_date, condition_received, reported_problem,
                 fault_details, accessories, technician_notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                num, data.get('customer_name',''), data.get('customer_phone',''), data.get('item_name',''),
                data.get('item_type',''), data.get('brand',''), data.get('model',''), data.get('serial_number',''),
                data.get('received_date',''), data.get('expected_date',''), data.get('condition_received',''),
                data.get('reported_problem',''), data.get('fault_details',''), data.get('accessories',''),
                data.get('technician_notes',''), data.get('status','Pending Approval')))
            conn.commit(); return cur.lastrowid
        except Exception:
            conn.rollback(); raise
        finally: conn.close()

    def update_repair_job(self, repair_id, data):
        conn = self.connect()
        try:
            conn.execute("""UPDATE repair_jobs SET customer_name=?, customer_phone=?, item_name=?, item_type=?,
                brand=?, model=?, serial_number=?, received_date=?, expected_date=?, condition_received=?,
                reported_problem=?, fault_details=?, accessories=?, technician_notes=?, status=? WHERE id=?""", (
                data.get('customer_name',''), data.get('customer_phone',''), data.get('item_name',''), data.get('item_type',''),
                data.get('brand',''), data.get('model',''), data.get('serial_number',''), data.get('received_date',''),
                data.get('expected_date',''), data.get('condition_received',''), data.get('reported_problem',''),
                data.get('fault_details',''), data.get('accessories',''), data.get('technician_notes',''),
                data.get('status','Pending Approval'), int(repair_id)))
            conn.commit()
        finally: conn.close()

    def get_repair_jobs(self, search=''):
        conn = self.connect()
        try:
            q = (search or '').strip()
            if q:
                like = f"%{q}%"
                return conn.execute("""SELECT r.*, COALESCE(e.total_amount,0) estimate_total,
                    a.bill_number actual_bill_number FROM repair_jobs r
                    LEFT JOIN repair_estimates e ON e.repair_id=r.id
                    LEFT JOIN repair_actual_bills a ON a.repair_id=r.id
                    WHERE r.repair_number LIKE ? OR r.customer_name LIKE ? OR r.customer_phone LIKE ?
                    OR r.item_name LIKE ? OR r.serial_number LIKE ? ORDER BY r.id DESC""",
                    (like,like,like,like,like)).fetchall()
            return conn.execute("""SELECT r.*, COALESCE(e.total_amount,0) estimate_total,
                a.bill_number actual_bill_number FROM repair_jobs r
                LEFT JOIN repair_estimates e ON e.repair_id=r.id
                LEFT JOIN repair_actual_bills a ON a.repair_id=r.id ORDER BY r.id DESC""").fetchall()
        finally: conn.close()

    def get_repair_job(self, repair_id):
        conn=self.connect()
        try: return conn.execute("SELECT * FROM repair_jobs WHERE id=?", (int(repair_id),)).fetchone()
        finally: conn.close()

    def find_repair_by_number(self, number):
        conn=self.connect()
        try: return conn.execute("SELECT * FROM repair_jobs WHERE repair_number=?", (str(number),)).fetchone()
        finally: conn.close()

    def save_repair_estimate(self, repair_id, items, labour_amount=0, other_charges=0, discount=0):
        conn=self.connect()
        try:
            cur=conn.cursor(); cur.execute("BEGIN")
            cur.execute("DELETE FROM repair_estimate_items WHERE repair_id=?", (int(repair_id),))
            material=0
            for x in items:
                qty=float(x.get('quantity',1)); cost=float(x.get('unit_cost',0)); total=qty*cost; material+=total
                cur.execute("INSERT INTO repair_estimate_items(repair_id,description,quantity,unit_cost,total) VALUES(?,?,?,?,?)", (int(repair_id),str(x.get('description','')).strip(),qty,cost,total))
            total=max(0,material+float(labour_amount)+float(other_charges)-float(discount))
            cur.execute("""INSERT INTO repair_estimates(repair_id,labour_amount,other_charges,discount,total_amount)
                VALUES(?,?,?,?,?) ON CONFLICT(repair_id) DO UPDATE SET labour_amount=excluded.labour_amount,
                other_charges=excluded.other_charges,discount=excluded.discount,total_amount=excluded.total_amount""",
                (int(repair_id),float(labour_amount),float(other_charges),float(discount),total))
            conn.commit()
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def get_repair_estimate(self, repair_id):
        conn=self.connect()
        try: return conn.execute("SELECT * FROM repair_estimates WHERE repair_id=?", (int(repair_id),)).fetchone()
        finally: conn.close()

    def get_repair_estimate_items(self, repair_id):
        conn=self.connect()
        try: return conn.execute("SELECT * FROM repair_estimate_items WHERE repair_id=? ORDER BY id", (int(repair_id),)).fetchall()
        finally: conn.close()

    def set_repair_status(self, repair_id, status):
        conn=self.connect()
        try:
            now = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if status == 'Approved': conn.execute("UPDATE repair_jobs SET status=?, approved_at=? WHERE id=?", (status,now,int(repair_id)))
            elif status == 'Delivered': conn.execute("UPDATE repair_jobs SET status=?, completed_at=? WHERE id=?", (status,now,int(repair_id)))
            else: conn.execute("UPDATE repair_jobs SET status=? WHERE id=?", (status,int(repair_id)))
            conn.commit()
        finally: conn.close()

    def create_repair_actual_bill(self, repair_id, data):
        conn=self.connect()
        try:
            cur=conn.cursor(); cur.execute("BEGIN IMMEDIATE")
            existing=cur.execute("SELECT bill_number FROM repair_actual_bills WHERE repair_id=?",(int(repair_id),)).fetchone()
            if existing: raise ValueError(f"Actual bill already exists: {existing['bill_number']}")
            row=cur.execute("SELECT id FROM repair_actual_bills ORDER BY id DESC LIMIT 1").fetchone()
            num=f"RINV-{((int(row['id'])+1) if row else 1):05d}"
            cur.execute("""INSERT INTO repair_actual_bills(repair_id,bill_number,labour_amount,other_charges,discount,total_amount,payment_method,amount_received,notes)
                VALUES(?,?,?,?,?,?,?,?,?)""",(int(repair_id),num,float(data.get('labour_amount',0)),float(data.get('other_charges',0)),float(data.get('discount',0)),float(data.get('total_amount',0)),str(data.get('payment_method','Cash')),float(data.get('amount_received',0)),str(data.get('notes',''))))
            for x in data.get('items',[]):
                qty=float(x.get('quantity',1)); cost=float(x.get('unit_cost',0))
                cur.execute("INSERT INTO repair_actual_items(repair_id,description,quantity,unit_cost,total) VALUES(?,?,?,?,?)",(int(repair_id),str(x.get('description','')),qty,cost,qty*cost))
            conn.commit(); return cur.lastrowid
        except Exception: conn.rollback(); raise
        finally: conn.close()

    def get_repair_actual(self, repair_id):
        conn=self.connect()
        try: return conn.execute("SELECT * FROM repair_actual_bills WHERE repair_id=?",(int(repair_id),)).fetchone()
        finally: conn.close()

    def get_repair_actual_items(self, repair_id):
        conn=self.connect()
        try: return conn.execute("SELECT * FROM repair_actual_items WHERE repair_id=? ORDER BY id",(int(repair_id),)).fetchall()
        finally: conn.close()



    def get_report_summary(self, start, end):
        """Return revenue, orders and product-based profit for a date range."""
        conn = self.connect()
        try:
            row = conn.execute("""
                SELECT
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COUNT(*) AS orders
                FROM sales
                WHERE created_at BETWEEN ? AND ?
            """, (start, end)).fetchone()

            profit_row = conn.execute("""
                SELECT COALESCE(SUM(
                    (
                        COALESCE(si.price, p.selling_price, 0)
                        - COALESCE(si.cost_price, p.purchase_price, 0)
                    ) * COALESCE(si.quantity, 0)
                ), 0) AS profit
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                LEFT JOIN products p ON p.id = si.product_id
                WHERE s.created_at BETWEEN ? AND ?
            """, (start, end)).fetchone()

            revenue = float(row["revenue"] or 0)
            orders = int(row["orders"] or 0)
            profit = float(profit_row["profit"] or 0)

            return {
                "sales": revenue,
                "revenue": revenue,
                "profit": profit,
                "orders": orders,
            }
        finally:
            conn.close()

    def get_sales_summary_report(self, start, end):
        """Return invoice-level sales rows for the Reports screen."""
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    invoice_number,
                    COALESCE(customer_name, 'Walk-in Customer') AS customer_name,
                    total_amount,
                    COALESCE(payment_method, 'Cash') AS payment_method,
                    created_at
                FROM sales
                WHERE created_at BETWEEN ? AND ?
                ORDER BY id DESC
            """, (start, end)).fetchall()
        finally:
            conn.close()

    def get_payment_methods_report(self, start, end):
        """Return sales grouped by payment method."""
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    COALESCE(payment_method, 'Cash') AS method,
                    COUNT(*) AS orders,
                    COALESCE(SUM(total_amount), 0) AS amount
                FROM sales
                WHERE created_at BETWEEN ? AND ?
                GROUP BY payment_method
                ORDER BY amount DESC
            """, (start, end)).fetchall()
        finally:
            conn.close()

    def get_low_stock_report(self):
        """Return products that are at or below their minimum stock."""
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT name, category, brand, stock, min_stock, unit
                FROM products
                WHERE stock <= min_stock
                ORDER BY stock ASC
            """).fetchall()
        finally:
            conn.close()

    def get_top_products_report(self, start, end, limit=50):
        """Return best-selling products for a date range."""
        conn = self.connect()
        try:
            return conn.execute("""
                SELECT
                    COALESCE(p.name, 'Unknown Product') AS product,
                    SUM(si.quantity) AS quantity,
                    COALESCE(SUM(
                        COALESCE(si.price, p.selling_price, 0)
                        * COALESCE(si.quantity, 0)
                    ), 0) AS amount
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                LEFT JOIN products p ON p.id = si.product_id
                WHERE s.created_at BETWEEN ? AND ?
                GROUP BY si.product_id
                ORDER BY quantity DESC
                LIMIT ?
            """, (start, end, int(limit))).fetchall()
        finally:
            conn.close()



if __name__ == "__main__":
    db = DatabaseManager()
    print("Database ready successfully!")
    print("Database:", db.db_path)
