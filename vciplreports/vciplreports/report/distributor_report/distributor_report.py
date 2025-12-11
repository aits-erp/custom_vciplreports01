import frappe
from frappe.utils import today, getdate, date_diff


def execute(filters=None):
    return get_columns(), get_data(filters)


# -------------------- COLUMNS -------------------- #
def get_columns():
    return [
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link",
         "options": "Customer Group", "width": 140},

        {"label": "Distributor", "fieldname": "customer", "fieldtype": "Link",
         "options": "Customer", "width": 200},

        {"label": "ASM", "fieldname": "asm", "fieldtype": "Link",
         "options": "Sales Person", "width": 150},

        {"label": "RSM", "fieldname": "rsm", "fieldtype": "Link",
         "options": "Sales Person", "width": 150},

        {"label": "Invoice Count", "fieldname": "invoice_count",
         "fieldtype": "Int", "width": 120},

        {"label": "Total Outstanding", "fieldname": "total_outstanding",
         "fieldtype": "Currency", "width": 150},

        {"label": "Total Overdue", "fieldname": "total_overdue",
         "fieldtype": "Currency", "width": 150},

        {"label": "Average Overdue Days", "fieldname": "avg_overdue_days",
         "fieldtype": "Float", "precision": 2, "width": 160},

        {"label": "Average Payment Days", "fieldname": "avg_payment_days",
         "fieldtype": "Float", "precision": 2, "width": 160},

        {"label": "Invoices", "fieldname": "invoices", "fieldtype": "Data", "hidden": 1}
    ]


# -------------------- MAIN DATA LOGIC -------------------- #
def get_data(filters=None):

    # ----------------------------------------------------
    # 1. FETCH SALES INVOICES
    # ----------------------------------------------------
    invoices = frappe.db.sql("""
        SELECT 
            si.name AS invoice,
            si.customer,
            si.customer_group,
            si.posting_date,
            si.outstanding_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.customer_group = 'Distributor'
        ORDER BY si.customer
    """, as_dict=True)

    if not invoices:
        return []

    # ----------------------------------------------------
    # 2. FETCH PAYMENT SCHEDULE (Due Dates)
    # ----------------------------------------------------
    payment_terms = frappe.db.sql("""
        SELECT parent, payment_amount, due_date
        FROM `tabPayment Schedule`
    """, as_dict=True)

    pay_map = {}
    for p in payment_terms:
        pay_map.setdefault(p.parent, []).append(p)

    # ----------------------------------------------------
    # 3. GROUP BY CUSTOMER + CALCULATE OVERDUE
    # ----------------------------------------------------
    cust_map = {}

    for inv in invoices:
        cust = inv.customer

        if cust not in cust_map:
            cust_map[cust] = {
                "customer_group": inv.customer_group,
                "customer": cust,
                "total_outstanding": 0,
                "total_overdue": 0,
                "invoices_detail": []
            }

        cust_map[cust]["total_outstanding"] += inv.outstanding_amount

        overdue_amount = 0
        overdue_days_list = []

        for term in pay_map.get(inv.invoice, []):
            if term.due_date and getdate(today()) > getdate(term.due_date):
                overdue_amount += term.payment_amount
                overdue_days_list.append(date_diff(today(), term.due_date))

        avg_overdue_days = (sum(overdue_days_list) / len(overdue_days_list)) if overdue_days_list else 0
        cust_map[cust]["total_overdue"] += overdue_amount

        cust_map[cust]["invoices_detail"].append({
            "invoice": inv.invoice,
            "posting_date": str(inv.posting_date),
            "outstanding": float(inv.outstanding_amount),
            "overdue": float(overdue_amount),
            "avg_overdue_days": avg_overdue_days
        })

    # ----------------------------------------------------
    # 4. FETCH PAYMENT ENTRY DATA (Actual Payment Dates)
    # ----------------------------------------------------
    payment_refs = frappe.db.sql("""
        SELECT 
            per.reference_name AS invoice,
            pe.posting_date AS payment_date
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE per.reference_doctype = 'Sales Invoice'
          AND pe.docstatus = 1
    """, as_dict=True)

    payment_map = {}
    for p in payment_refs:
        payment_map.setdefault(p.invoice, []).append(p.payment_date)

    # ----------------------------------------------------
    # 5. FETCH SALES TEAM (ASM / RSM)
    # ----------------------------------------------------
    sales_team = frappe.db.get_all(
        "Sales Team",
        filters={"parenttype": "Customer"},
        fields=["parent", "sales_person"]
    )
    sales_map = {s.parent: s.sales_person for s in sales_team}

    # ----------------------------------------------------
    # 6. IDENTIFY ASM / RSM THROUGH SALES PERSON TREE
    # ----------------------------------------------------
    for cust, row in cust_map.items():

        sp = sales_map.get(cust)
        asm = None
        rsm = None

        while sp:
            parent_sp = frappe.db.get_value("Sales Person", sp, "parent_sales_person")
            if not parent_sp:
                break

            # Find ASM person
            if parent_sp.startswith("ASM"):
                asm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent_sp, "is_group": 0},
                    "name"
                )

            # Find RSM person
            if parent_sp.startswith("RSM"):
                rsm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent_sp, "is_group": 0},
                    "name"
                )

            sp = parent_sp

        row["asm"] = asm
        row["rsm"] = rsm

    # ----------------------------------------------------
    # 7. FINAL RESULT COMPILATION
    # ----------------------------------------------------
    result = []

    for cust, row in cust_map.items():

        # Overdue day average (already stored)
        overdue_days_list = [i["avg_overdue_days"] for i in row["invoices_detail"]]
        avg_days_customer = (sum(overdue_days_list) / len(overdue_days_list)) if overdue_days_list else 0

        # ---------------- AVERAGE PAYMENT DAYS ---------------- #
        payment_days_list = []

        for inv in row["invoices_detail"]:
            invoice_date = getdate(inv["posting_date"])
            payments = payment_map.get(inv["invoice"], [])

            for pay_date in payments:
                payment_days_list.append(date_diff(pay_date, invoice_date))

        avg_payment_days = (sum(payment_days_list) / len(payment_days_list)) if payment_days_list else 0

        # ---------------- FINAL ROW ---------------- #
        result.append({
            "customer_group": row["customer_group"],
            "customer": cust,
            "asm": row["asm"],
            "rsm": row["rsm"],
            "invoice_count": len(row["invoices_detail"]),
            "total_outstanding": row["total_outstanding"],
            "total_overdue": row["total_overdue"],
            "avg_overdue_days": avg_days_customer,
            "avg_payment_days": avg_payment_days,
            "invoices": frappe.as_json(row["invoices_detail"])
        })

    return result
