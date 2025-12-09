import frappe
from frappe.utils import today, getdate

def execute(filters=None):
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Data", "width": 120},
        {"label": "Distributor Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},

        # CLICKABLE ASM & RSM
        {"label": "ASM", "fieldname": "asm", "fieldtype": "Link", "options": "Sales Person", "width": 150},
        {"label": "RSM", "fieldname": "rsm", "fieldtype": "Link", "options": "Sales Person", "width": 150},

        {"label": "Total Outstanding Amount", "fieldname": "total_outstanding", "fieldtype": "Currency", "width": 180},
        {"label": "Total Overdue Amount", "fieldname": "total_overdue", "fieldtype": "Currency", "width": 180},
    ]


def get_data(filters):

    invoices = frappe.db.sql("""
        SELECT 
            si.name AS invoice,
            si.customer,
            si.customer_name,
            si.customer_group,
            si.outstanding_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.customer_group = 'Distributor'
    """, as_dict=True)

    customer_map = {}

    for inv in invoices:

        if inv.customer not in customer_map:
            customer_map[inv.customer] = {
                "customer_group": inv.customer_group,
                "customer_name": inv.customer_name,
                "total_outstanding": 0,
                "total_overdue": 0,
                "asm": None,
                "rsm": None
            }

        # Total Outstanding
        customer_map[inv.customer]["total_outstanding"] += inv.outstanding_amount

        # Payment Terms Overdue Logic
        payment_terms = frappe.db.sql("""
            SELECT payment_amount, due_date 
            FROM `tabPayment Schedule`
            WHERE parent = %s
        """, (inv.invoice,), as_dict=True)

        overdue = 0
        for term in payment_terms:
            if term.due_date and getdate(today()) > getdate(term.due_date):
                overdue += term.payment_amount

        customer_map[inv.customer]["total_overdue"] += overdue


    # ---- FIND ASM & RSM BY CLIMBING THE TREE ----
    for cust, row in customer_map.items():

        sales_person = frappe.db.get_value(
            "Sales Team",
            {"parent": cust, "parenttype": "Customer"},
            "sales_person"
        )

        asm = None
        rsm = None

        current = sales_person

        while current:
            parent = frappe.db.get_value("Sales Person", current, "parent_sales_person")

            if not parent:
                break

            # Identify ASM
            if parent.startswith("ASM"):
                asm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent, "is_group": 0},
                    "name"
                )

            # Identify RSM
            if parent.startswith("RSM"):
                rsm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent, "is_group": 0},
                    "name"
                )

            current = parent

        row["asm"] = asm
        row["rsm"] = rsm

    return list(customer_map.values())
