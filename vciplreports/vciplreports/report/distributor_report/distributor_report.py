import frappe
from frappe.utils import today, getdate

def execute(filters=None):
    return get_columns(), get_data(filters)

def get_columns():
    return [
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Data", "width": 120},
        {"label": "Distributor Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": "ASM", "fieldname": "asm", "fieldtype": "Data", "width": 140},
        {"label": "RSM", "fieldname": "rsm", "fieldtype": "Data", "width": 140},
        {"label": "Invoice", "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 120},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
        {"label": "Overdue Days", "fieldname": "overdue_days", "fieldtype": "Int", "width": 90},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Total Overdue", "fieldname": "total_overdue", "fieldtype": "Currency", "width": 130},
    ]


def get_data(filters):

    invoices = frappe.db.sql("""
        SELECT 
            si.name AS invoice,
            si.customer,
            si.customer_name,
            si.customer_group,
            si.posting_date,
            si.due_date,
            si.outstanding_amount,
            ste.sales_person
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Team` ste ON ste.parent = si.name
        WHERE si.docstatus = 1
          AND si.customer_group = 'Distributor'
    """, as_dict=True)

    data = []

    for inv in invoices:

        asm = rsm = None

        # Step 1: Sales Person (TSO)
        sales_person = inv.sales_person

        # Step 2: Parent of Sales Person = ASM
        parent1 = frappe.db.get_value("Sales Person", sales_person, "parent_sales_person")

        # Step 3: Parent of ASM = RSM
        parent2 = frappe.db.get_value("Sales Person", parent1, "parent_sales_person")

        asm = parent1
        rsm = parent2

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
            "invoice": inv.invoice,
            "posting_date": inv.posting_date,
            "due_date": inv.due_date,
            "overdue_days": overdue_days,
            "outstanding_amount": inv.outstanding_amount,
            "total_overdue": total_overdue
        })

    return data
