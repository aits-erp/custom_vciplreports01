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
        {"label": "Overdue Days", "fieldname": "overdue_days", "fieldtype": "Int", "width": 100},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Total Overdue", "fieldname": "total_overdue", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):

    invoices = frappe.db.sql("""
        SELECT 
            si.name AS invoice,
            si.customer,
            si.customer_name,
            si.customer_group,
            si.due_date,
            si.outstanding_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
          AND si.customer_group = 'Distributor'
    """, as_dict=True)

    data = []

    for inv in invoices:

        # Fetch Sales Person assigned to Customer (TSO)
        tso = frappe.db.get_value(
            "Sales Team",
            {"parent": inv.customer, "parenttype": "Customer"},
            "sales_person"
        )

        asm = rsm = None

        if tso:
            # Parent of TSO = ASM
            asm = frappe.db.get_value("Sales Person", tso, "parent_sales_person")

            # Parent of ASM = RSM
            if asm:
                rsm = frappe.db.get_value("Sales Person", asm, "parent_sales_person")

        # Overdue calculation
        overdue_days = 0
        total_overdue = 0

        if inv.due_date and getdate(today()) > getdate(inv.due_date):
            overdue_days = (getdate(today()) - getdate(inv.due_date)).days
            total_overdue = inv.outstanding_amount

        data.append({
            "customer_group": inv.customer_group,
            "customer_name": inv.customer_name,
            "asm": asm,
            "rsm": rsm,
            "overdue_days": overdue_days,
            "outstanding_amount": inv.outstanding_amount,
            "total_overdue": total_overdue
        })

    return data
