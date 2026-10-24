import os
from datetime import datetime

from reportlab.lib.pagesizes import A4, A5, A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_invoice(
    invoice_number,
    cart_items,
    total_amount,
    payment_method="Cash",
    customer_name="",
    customer_phone="",
    subtotal=0,
    labour_amount=0,
    discount=0,
    cash_received=0,
    change=0,
    paper_size="A4"
):
    """
    Generate ElectroSmart invoice.

    Supported paper sizes:
        A4
        A5
        A6
        Thermal 80mm
        Thermal 58mm

    Returns:
        str: Generated PDF file path
    """

    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    reports_dir = os.path.join(
        base_dir,
        "reports"
    )

    assets_dir = os.path.join(
        base_dir,
        "assets"
    )

    os.makedirs(
        reports_dir,
        exist_ok=True
    )

    file_path = os.path.join(
        reports_dir,
        f"{invoice_number}.pdf"
    )


    logo_path = os.path.join(
        assets_dir,
        "LOGO.png"
    )


    paper_sizes = {
        "A4": A4,
        "A5": A5,
        "A6": A6,

        "Thermal 80mm": (
            80 * mm,
            200 * mm
        ),

        "Thermal 58mm": (
            58 * mm,
            180 * mm
        )
    }

    if paper_size not in paper_sizes:
        paper_size = "A4"

    page_width, page_height = paper_sizes[paper_size]

    pdf = canvas.Canvas(
        file_path,
        pagesize=(page_width, page_height)
    )


    dark_color = "#1E293B"
    gray_color = "#64748B"
    line_color = "#CBD5E1"


    try:
        subtotal = float(subtotal)
    except (TypeError, ValueError):
        subtotal = 0

    try:
        labour_amount = float(labour_amount)
    except (TypeError, ValueError):
        labour_amount = 0

    try:
        discount = float(discount)
    except (TypeError, ValueError):
        discount = 0

    try:
        total_amount = float(total_amount)
    except (TypeError, ValueError):
        total_amount = 0

    try:
        cash_received = float(cash_received)
    except (TypeError, ValueError):
        cash_received = 0

    try:
        change = float(change)
    except (TypeError, ValueError):
        change = 0


    if paper_size == "A4":
        margin = 20 * mm
    elif paper_size == "A5":
        margin = 15 * mm
    elif paper_size == "A6":
        margin = 8 * mm
    elif paper_size == "Thermal 80mm":
        margin = 4 * mm
    else:
        margin = 3 * mm

    left = margin
    right = page_width - margin

    content_width = right - left


    if paper_size == "A4":
        shop_font = 22
        normal_font = 10
        table_font = 9
    elif paper_size == "A5":
        shop_font = 17
        normal_font = 9
        table_font = 8
    elif paper_size == "A6":
        shop_font = 12
        normal_font = 7
        table_font = 6.5
    elif paper_size == "Thermal 80mm":
        shop_font = 10
        normal_font = 7
        table_font = 6.5
    else:
        shop_font = 8
        normal_font = 6
        table_font = 5.5


    y = page_height - 10 * mm


    if os.path.exists(logo_path):

        if paper_size in ["A4", "A5"]:
            logo_width = 18 * mm
            logo_height = 18 * mm

        elif paper_size == "A6":
            logo_width = 12 * mm
            logo_height = 12 * mm

        else:
            logo_width = 9 * mm
            logo_height = 9 * mm

        pdf.drawImage(
            ImageReader(logo_path),
            left,
            y - logo_height,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            anchor="nw",
            mask="auto"
        )

        y -= logo_height + 5 * mm


    pdf.setFillColor(dark_color)

    pdf.setFont(
        "Helvetica-Bold",
        shop_font
    )

    shop_name = (
        "Nadeem Shahanvi Electrical & Electronics Care Centre"
    )

    if paper_size in [
        "A6",
        "Thermal 80mm",
        "Thermal 58mm"
    ]:
        shop_name = "Nadeem Shahanvi Electrical & Electronics Care Centre"

    pdf.drawCentredString(
        page_width / 2,
        y,
        shop_name
    )

    y -= 5 * mm


    pdf.setFont(
        "Helvetica",
        normal_font
    )

    pdf.setFillColor(gray_color)

    if paper_size not in [
        "Thermal 80mm",
        "Thermal 58mm"
    ]:

        pdf.drawCentredString(
            page_width / 2,
            y,
            "Electrical Items • Fans • Capacitors • Cables"
        )

        y -= 5 * mm


    pdf.drawCentredString(
        page_width / 2,
        y,
        "Phone: 0302-4420051 | 0300-4644413"
    )

    y -= 6 * mm


    pdf.setStrokeColor(line_color)

    pdf.line(
        left,
        y,
        right,
        y
    )

    y -= 6 * mm


    now = datetime.now()

    pdf.setFillColor(dark_color)

    pdf.setFont(
        "Helvetica-Bold",
        normal_font
    )

    
    pdf.drawString(
        left,
        y,
        "POS: 01"
    )

    pdf.drawRightString(
        right,
        y,
        f"Receipt #: {invoice_number}"
    )

    y -= 5 * mm
    

    pdf.setFont(
        "Helvetica",
        normal_font
    )

    pdf.drawString(
        left,
        y,
        f"Date: {now.strftime('%d-%m-%Y')}"
    )

    pdf.drawRightString(
        right,
        y,
        f"Time: {now.strftime('%I:%M %p')}"
    )

    y -= 5 * mm

    safe_customer_name = str(
        customer_name
    ).strip()

    if not safe_customer_name:
        safe_customer_name = ""

    max_name_length = (
        28
        if paper_size == "A4"
        else 20
    )

    if len(safe_customer_name) > max_name_length:
        safe_customer_name = (
            safe_customer_name[:max_name_length]
            + ".."
        )

    pdf.drawString(
        left,
        y,
        f"Customer: {safe_customer_name}"
    )

    y -= 5 * mm


    safe_customer_phone = str(
        customer_phone
    ).strip()

    if safe_customer_phone:
        pdf.drawString(
            left,
            y,
            f"Phone: {safe_customer_phone}"
        )
    else:
        pdf.drawString(
            left,
            y,
            "Phone: Not Provided"
        )

    y -= 7 * mm


    pdf.setStrokeColor(dark_color)

    pdf.line(
        left,
        y,
        right,
        y
    )

    y -= 5 * mm

    pdf.setFillColor(dark_color)

    pdf.setFont(
        "Helvetica-Bold",
        table_font
    )

    if paper_size == "A4":

        col_sr = left
        col_product = left + 12 * mm
        col_qty = left + 105 * mm
        col_price = left + 130 * mm
        col_discount = left + 155 * mm
        col_amount = right

        show_discount = True

    elif paper_size == "A5":

        col_sr = left
        col_product = left + 10 * mm
        col_qty = left + 65 * mm
        col_price = left + 85 * mm
        col_discount = left + 102 * mm
        col_amount = right

        show_discount = True

    elif paper_size == "A6":

        col_sr = left
        col_product = left + 7 * mm
        col_qty = left + 35 * mm
        col_price = left + 48 * mm
        col_amount = right

        show_discount = False

    elif paper_size == "Thermal 80mm":

        col_sr = left
        col_product = left + 8 * mm
        col_qty = left + 35 * mm
        col_price = left + 50 * mm
        col_amount = right

        show_discount = False

    else:

        col_sr = left
        col_product = left + 6 * mm
        col_qty = left + 25 * mm
        col_price = left + 36 * mm
        col_amount = right

        show_discount = False


    pdf.drawString(
        col_sr,
        y,
        "Sr."
    )

    pdf.drawString(
        col_product,
        y,
        "Product"
    )

    pdf.drawRightString(
        col_qty,
        y,
        "Qty"
    )

    pdf.drawRightString(
        col_price,
        y,
        "Price"
    )

    if show_discount:

        pdf.drawRightString(
            col_discount,
            y,
            "Disc %"
        )

    pdf.drawRightString(
        col_amount,
        y,
        "Amount"
    )

    y -= 4 * mm

    pdf.setStrokeColor(line_color)

    pdf.line(
        left,
        y,
        right,
        y
    )

    y -= 5 * mm


    pdf.setFillColor(dark_color)

    pdf.setFont(
        "Helvetica",
        table_font
    )

    for index, item in enumerate(
        cart_items,
        start=1
    ):

        name = str(
            item.get(
                "name",
                "Unknown Item"
            )
        )

        if paper_size == "A4":
            max_product_length = 28
        elif paper_size == "A5":
            max_product_length = 20
        elif paper_size == "A6":
            max_product_length = 13
        elif paper_size == "Thermal 80mm":
            max_product_length = 16
        else:
            max_product_length = 10

        if len(name) > max_product_length:
            name = (
                name[:max_product_length]
                + ".."
            )

        try:
            price = float(
                item.get(
                    "price",
                    0
                )
            )
        except (
            TypeError,
            ValueError
        ):
            price = 0

        try:
            quantity = int(
                item.get(
                    "quantity",
                    0
                )
            )
        except (
            TypeError,
            ValueError
        ):
            quantity = 0

        item_amount = (
            price * quantity
        )

        pdf.drawString(
            col_sr,
            y,
            str(index)
        )

        pdf.drawString(
            col_product,
            y,
            name
        )

        pdf.drawRightString(
            col_qty,
            y,
            str(quantity)
        )

        pdf.drawRightString(
            col_price,
            y,
            f"{price:,.2f}"
        )

        if show_discount:

            pdf.drawRightString(
                col_discount,
                y,
                "0"
            )
        pdf.drawRightString(
            col_amount,
            y,
            f"{item_amount:,.2f}"
        )

        y -= 5 * mm

        pdf.setStrokeColor(line_color)

        pdf.line(
            left,
            y + 1.5 * mm,
            right,
            y + 1.5 * mm
        )


    total_quantity = 0

    for item in cart_items:

        try:
            total_quantity += int(
                item.get(
                    "quantity",
                    0
                )
            )
        except (
            TypeError,
            ValueError
        ):
            pass

    y -= 2 * mm

    pdf.setFillColor(dark_color)

    pdf.setFont(
        "Helvetica-Bold",
        normal_font
    )

    pdf.drawRightString(
        col_qty,
        y,
        str(total_quantity)
    )

    pdf.drawRightString(
        col_amount,
        y,
        f"{subtotal:,.2f}"
    )

    y -= 6 * mm

    pdf.setStrokeColor(dark_color)

    pdf.line(
        left,
        y,
        right,
        y
    )

    y -= 7 * mm

    if paper_size == "A4":
        summary_left = left + 95 * mm
    elif paper_size == "A5":
        summary_left = left + 65 * mm
    else:
        summary_left = left

    summary_right = right

    pdf.setFont(
        "Helvetica",
        normal_font
    )

    pdf.setFillColor(dark_color)


    pdf.drawString(
        summary_left,
        y,
        "Subtotal:"
    )

    pdf.drawRightString(
        summary_right,
        y,
        f"Rs. {subtotal:,.2f}"
    )

    y -= 5 * mm


    pdf.drawString(
        summary_left,
        y,
        "Labour Charges:"
    )

    pdf.drawRightString(
        summary_right,
        y,
        f"Rs. {labour_amount:,.2f}"
    )

    y -= 5 * mm


    pdf.drawString(
        summary_left,
        y,
        "Discount:"
    )

    pdf.drawRightString(
        summary_right,
        y,
        f"Rs. {discount:,.2f}"
    )

    y -= 6 * mm


    pdf.setFont(
        "Helvetica-Bold",
        normal_font + 2
    )

    pdf.drawString(
        summary_left,
        y,
        "GRAND TOTAL:"
    )

    pdf.drawRightString(
        summary_right,
        y,
        f"Rs. {total_amount:,.2f}"
    )

    y -= 7 * mm

    pdf.setFont(
        "Helvetica-Bold",
        normal_font
    )

    pdf.drawString(
        summary_left,
        y,
        f"Payment: {payment_method}"
    )

    y -= 5 * mm

    if str(payment_method).lower() == "cash":

        pdf.setFont(
            "Helvetica",
            normal_font
        )

        pdf.drawString(
            summary_left,
            y,
            "Cash Received:"
        )

        pdf.drawRightString(
            summary_right,
            y,
            f"Rs. {cash_received:,.2f}"
        )

        y -= 5 * mm

        pdf.drawString(
            summary_left,
            y,
            "Balance:"
        )

        pdf.drawRightString(
            summary_right,
            y,
            f"Rs. {change:,.2f}"
        )

        y -= 5 * mm

    elif str(payment_method).lower() == "credit":

        pdf.setFont(
            "Helvetica-Bold",
            normal_font
        )

        pdf.drawString(
            summary_left,
            y,
            "Payment Status: CREDIT"
        )

        y -= 5 * mm

    y -= 4 * mm

    pdf.setFillColor(gray_color)

    pdf.setFont(
        "Helvetica",
        normal_font
    )

    pdf.drawString(
        left,
        y,
        "Sales Person: Admin"
    )

    y -= 6 * mm

    pdf.setStrokeColor(line_color)

    pdf.line(
        left,
        y,
        right,
        y
    )

    y -= 7 * mm

    pdf.setFillColor(dark_color)

    pdf.setFont(
        "Helvetica-Bold",
        normal_font + 1
    )

    pdf.drawCentredString(
        page_width / 2,
        y,
        "Thank You For Your Visit!"
    )

    y -= 5 * mm

    pdf.setFont(
        "Helvetica",
        normal_font
    )

    pdf.setFillColor(gray_color)

    pdf.drawCentredString(
        page_width / 2,
        y,
        "Please Visit Again"
    )

    y -= 5 * mm

    pdf.drawCentredString(
        page_width / 2,
        y,
        "Software prepared by -----"
    )


    pdf.save()

    return file_path