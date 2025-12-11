import frappe

def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Customer Group", "fieldname": "customer_group", "fieldtype": "Link",
         "options": "Customer Group", "width": 150},

        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link",
         "options": "Customer", "width": 220},

        {"label": "Invoice Count", "fieldname": "invoice_count",
         "fieldtype": "Int", "width": 130},

        {"label": "Total Amount", "fieldname": "total_amount",
         "fieldtype": "Currency", "width": 160}
    ]


def get_data(filters):
    sql = """
        SELECT 
            si.customer_group,
            si.customer,
            COUNT(si.name) AS invoice_count,
            SUM(si.grand_total) AS total_amount
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
    """

    values = []

    if filters.get("company"):
        sql += " AND si.company = %s"
        values.append(filters.get("company"))

    if filters.get("year"):
        sql += " AND YEAR(si.posting_date) = %s"
        values.append(int(filters.get("year")))

    sql += " GROUP BY si.customer ORDER BY si.customer"

    return frappe.db.sql(sql, values, as_dict=True)


# ============ MONTH-WISE BREAKUP POPUP ============ #

@frappe.whitelist()
def get_month_breakup(customer, company=None, year=None):
    sql = """
        SELECT 
            DATE_FORMAT(posting_date, '%%b') AS month,
            SUM(grand_total) AS amount
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND customer = %s
    """

    values = [customer]

    if company:
        sql += " AND company = %s"
        values.append(company)

    if year:
        sql += " AND YEAR(posting_date) = %s"
        values.append(int(year))

    sql += " GROUP BY MONTH(posting_date) ORDER BY MONTH(posting_date)"

    data = frappe.db.sql(sql, tuple(values), as_dict=True)

    if not data:
        return "<b>No data found</b>"

    html = "<h4>Month-wise Sales</h4>"
    html += "<table class='table table-bordered'>"
    html += "<tr><th>Month</th><th>Amount</th></tr>"

    for d in data:
        html += f"<tr><td>{d.month}</td><td>{frappe.utils.fmt_money(d.amount)}</td></tr>"

    html += "</table>"
    return html
