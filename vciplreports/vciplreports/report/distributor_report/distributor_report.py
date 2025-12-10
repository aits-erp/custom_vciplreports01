import frappe
from frappe.utils import today, getdate, date_diff


def execute(filters=None):
    return get_columns(), get_data(filters)


# -------------------- COLUMNS -------------------- #
def get_columns():
    return [
        {
            "label": "Customer Group",
            "fieldname": "customer_group",
            "fieldtype": "Link",
            "options": "Customer Group",
            "width": 140
        },
        {
            "label": "Distributor",
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": "ASM",
            "fieldname": "asm",
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 150
        },
        {
            "label": "RSM",
            "fieldname": "rsm",
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 150
        },
        {
            "label": "Invoice Count",
            "fieldname": "invoice_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Total Outstanding",
            "fieldname": "total_outstanding",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Total Overdue",
            "fieldname": "total_overdue",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Average Overdue Days",
            "fieldname": "avg_overdue_days",
            "fieldtype": "Float",
            "precision": 2,
            "width": 180
        },
        {
            "label": "Invoices",
            "fieldname": "invoices",
            "fieldtype": "Data",
            "hidden": 1
        }
    ]


# -------------------- MAIN DATA LOGIC -------------------- #
def get_data(filters=None):

    # Fetch invoices
    invoices = frappe.db.sql("""
        SELECT 
            si.name AS invoice,
            si.customer,
            si.customer_name,
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

    # Fetch payment terms
    payment_terms = frappe.db.sql("""
        SELECT parent, payment_amount, due_date
        FROM `tabPayment Schedule`
    """, as_dict=True)

    pay_map = {}
    for p in payment_terms:
        pay_map.setdefault(p.parent, []).append(p)

    # Group data by customer
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

        # outstanding
        cust_map[cust]["total_outstanding"] += inv.outstanding_amount

        # overdue calculation
        overdue_amount = 0
        overdue_days_list = []

        for t in pay_map.get(inv.invoice, []):
            if t.due_date and getdate(today()) > getdate(t.due_date):
                overdue_amount += t.payment_amount
                overdue_days_list.append(date_diff(today(), t.due_date))

        # average overdue days for this invoice
        avg_overdue_days = (
            sum(overdue_days_list) / len(overdue_days_list)
            if overdue_days_list else 0
        )

        cust_map[cust]["total_overdue"] += overdue_amount

        # store invoice info
        cust_map[cust]["invoices_detail"].append({
            "invoice": inv.invoice,
            "posting_date": str(inv.posting_date),
            "outstanding": float(inv.outstanding_amount),
            "overdue": float(overdue_amount),
            "avg_overdue_days": avg_overdue_days
        })

    # Load Sales Team relation
    sales_team = frappe.db.get_all(
        "Sales Team",
        filters={"parenttype": "Customer"},
        fields=["parent", "sales_person"]
    )

    sales_map = {s.parent: s.sales_person for s in sales_team}

    # ---------- UPDATED ASM & RSM LOGIC (REAL PERSON NAME) ---------- #
    for cust, row in cust_map.items():

        current = sales_map.get(cust)
        asm = None
        rsm = None

        while current:

            parent = frappe.db.get_value("Sales Person", current, "parent_sales_person")

            if not parent:
                break

            # If parent is ASM group → fetch actual name
            if parent.startswith("ASM"):
                asm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent, "is_group": 0},
                    "name"
                )

            # If parent is RSM group → fetch actual name
            if parent.startswith("RSM"):
                rsm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent, "is_group": 0},
                    "name"
                )

            current = parent

        row["asm"] = asm
        row["rsm"] = rsm

    # Prepare final rows
    result = []

    for cust, row in cust_map.items():

        # Customer-level average overdue days
        invoice_days = [i["avg_overdue_days"] for i in row["invoices_detail"]]
        avg_days_customer = sum(invoice_days) / len(invoice_days) if invoice_days else 0

        result.append({
            "customer_group": row["customer_group"],
            "customer": cust,
            "asm": row["asm"],
            "rsm": row["rsm"],
            "invoice_count": len(row["invoices_detail"]),
            "total_outstanding": row["total_outstanding"],
            "total_overdue": row["total_overdue"],
            "avg_overdue_days": avg_days_customer,
            "invoices": frappe.as_json(row["invoices_detail"])
        })

    return result
