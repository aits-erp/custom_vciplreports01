import frappe
from frappe.utils import today, getdate, date_diff


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


# -------------------- COLUMNS -------------------- #
def get_columns():
    return [
        {
            "label": "Node",
            "fieldname": "entity",
            "fieldtype": "Data",
            "width": 250
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
            "width": 150
        },
        {
            "label": "ASM",
            "fieldname": "asm",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "RSM",
            "fieldname": "rsm",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Indent",
            "fieldname": "indent",
            "hidden": 1
        },
        {
            "label": "Parent",
            "fieldname": "parent_node",
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

    # Payment terms map
    payment_terms = frappe.db.sql("""
        SELECT parent, payment_amount, due_date
        FROM `tabPayment Schedule`
    """, as_dict=True)

    pay_map = {}
    for p in payment_terms:
        pay_map.setdefault(p.parent, []).append(p)

    # Group by customer
    cust_map = {}

    for inv in invoices:
        cust = inv.customer

        if cust not in cust_map:
            cust_map[cust] = {
                "customer_group": inv.customer_group,
                "customer": cust,
                "invoices": [],
                "total_outstanding": 0,
                "total_overdue": 0,
            }

        cust_map[cust]["total_outstanding"] += inv.outstanding_amount

        overdue_amount = 0
        overdue_days_list = []

        # overdue logic
        for t in pay_map.get(inv.invoice, []):
            if t.due_date and getdate(today()) > getdate(t.due_date):
                overdue_amount += t.payment_amount
                overdue_days_list.append(date_diff(today(), t.due_date))

        avg_due_days = sum(overdue_days_list) / len(overdue_days_list) if overdue_days_list else 0

        cust_map[cust]["total_overdue"] += overdue_amount

        cust_map[cust]["invoices"].append({
            "invoice": inv.invoice,
            "posting": str(inv.posting_date),
            "due": overdue_amount,
            "avg_days": avg_due_days,
            "outstanding": inv.outstanding_amount
        })

    # Sales Person Mapping
    sales_map = {}
    for s in frappe.get_all("Sales Team", filters={"parenttype": "Customer"}, fields=["parent", "sales_person"]):
        sales_map[s.parent] = s.sales_person

    # Identify ASM / RSM
    for cust, row in cust_map.items():

        sp = sales_map.get(cust)
        asm = None
        rsm = None

        while sp:
            parent = frappe.db.get_value("Sales Person", sp, "parent_sales_person")
            if not parent:
                break

            if parent.startswith("ASM"):
                asm = frappe.db.get_value("Sales Person", {"parent_sales_person": parent, "is_group": 0}, "name")

            if parent.startswith("RSM"):
                rsm = frappe.db.get_value("Sales Person", {"parent_sales_person": parent, "is_group": 0}, "name")

            sp = parent

        row["asm"] = asm
        row["rsm"] = rsm

    # ---------------- DRILL DOWN STRUCTURE ---------------- #
    final_data = []

    # Step 1: Add Customer Group as top-level node
    groups = {}

    for cust, row in cust_map.items():
        grp = row["customer_group"]
        groups.setdefault(grp, []).append(row)

    for grp, customers in groups.items():

        # GROUP ROW
        final_data.append({
            "entity": grp,
            "invoice_count": sum(len(r["invoices"]) for r in customers),
            "total_outstanding": sum(r["total_outstanding"] for r in customers),
            "total_overdue": sum(r["total_overdue"] for r in customers),
            "avg_overdue_days": 0,
            "asm": "",
            "rsm": "",
            "indent": 0,
            "parent_node": None
        })

        # Step 2: Customer Rows
        for row in customers:

            avg_days_customer = sum(i["avg_days"] for i in row["invoices"]) / len(row["invoices"]) if row["invoices"] else 0

            final_data.append({
                "entity": row["customer"],
                "invoice_count": len(row["invoices"]),
                "total_outstanding": row["total_outstanding"],
                "total_overdue": row["total_overdue"],
                "avg_overdue_days": avg_days_customer,
                "asm": row["asm"],
                "rsm": row["rsm"],
                "indent": 1,
                "parent_node": grp
            })

            # Step 3: Invoice Drill Rows
            for inv in row["invoices"]:
                final_data.append({
                    "entity": "🧾 " + inv["invoice"],
                    "invoice_count": 1,
                    "total_outstanding": inv["outstanding"],
                    "total_overdue": inv["due"],
                    "avg_overdue_days": inv["avg_days"],
                    "asm": "",
                    "rsm": "",
                    "indent": 2,
                    "parent_node": row["customer"]
                })

    return final_data
