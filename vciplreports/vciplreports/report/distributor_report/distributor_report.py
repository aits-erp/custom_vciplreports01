import frappe
from frappe.utils import today, getdate

def execute(filters=None):
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Data", "width": 120},
        {"label": "Distributor Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
        {"label": "ASM", "fieldname": "asm", "fieldtype": "Data", "width": 150},
        {"label": "RSM", "fieldname": "rsm", "fieldtype": "Data", "width": 150},
        {"label": "Total Outstanding Amount", "fieldname": "total_outstanding", "fieldtype": "Currency", "width": 180},
        {"label": "Total Overdue Amount", "fieldname": "total_overdue", "fieldtype": "Currency", "width": 180},
    ]


def get_data(filters):

    # Fetch all invoices for Distributor customers
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

    # Group values by Customer
    customer_map = {}

    for inv in invoices:

        if inv.customer not in customer_map:
            customer_map[inv.customer] = {
                "customer_group": inv.customer_group,
                "customer_name": inv.customer_name,
                "total_outstanding": 0,
                "total_overdue": 0,
                "asm": "-",
                "rsm": "-"
            }

        # ------ 1️⃣ TOTAL OUTSTANDING (simple sum of outstanding) ------
        customer_map[inv.customer]["total_outstanding"] += inv.outstanding_amount

        # ------ 2️⃣ TOTAL OVERDUE BASED ON PAYMENT TERMS ------
        payment_terms = frappe.db.sql("""
            SELECT payment_amount, due_date 
            FROM `tabPayment Schedule`
            WHERE parent = %s
        """, (inv.invoice,), as_dict=True)

        overdue_amount = 0

        for term in payment_terms:
            if term.due_date and getdate(today()) > getdate(term.due_date):
                overdue_amount += term.payment_amount

        customer_map[inv.customer]["total_overdue"] += overdue_amount

    # ------ 3️⃣ GET ASM & RSM BASED ON CUSTOMER'S SALES PERSON ------
    for cust in customer_map:

        # Sales Person from Customer → Sales Team table
        sales_person = frappe.db.get_value(
            "Sales Team",
            {"parent": cust, "parenttype": "Customer"},
            "sales_person"
        )

        asm = "-"
        rsm = "-"

        if sales_person:

            parent_group = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")

            # CASE 1 → Sales Person under ASM group
            if parent_group and parent_group.startswith("ASM"):

                asm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent_group, "is_group": 0},
                    "name"
                )

                rsm_group = frappe.db.get_value("Sales Person", parent_group, "parent_sales_person")

                rsm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": rsm_group, "is_group": 0},
                    "name"
                )

            # CASE 2 → Sales Person directly under RSM group
            elif parent_group and parent_group.startswith("RSM"):

                rsm = frappe.db.get_value(
                    "Sales Person",
                    {"parent_sales_person": parent_group, "is_group": 0},
                    "name"
                )

                asm = "-"

        customer_map[cust]["asm"] = asm
        customer_map[cust]["rsm"] = rsm

    # Return as list
    return list(customer_map.values())
