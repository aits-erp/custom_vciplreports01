import frappe

def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Supplier Group", "fieldname": "supplier_group", "fieldtype": "Link",
         "options": "Supplier Group", "width": 150},

        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data",
         "width": 220},

        {"label": "Purchase Count", "fieldname": "invoice_count",
         "fieldtype": "Int", "width": 130},

        {"label": "Total Amount", "fieldname": "total_amount",
         "fieldtype": "Currency", "width": 160}
    ]


def get_data(filters):
    sql = """
        SELECT 
            pi.supplier_group,
            CONCAT('<a href="#" class="supplier-link" data-supplier="', pi.supplier, '">', pi.supplier, '</a>') AS supplier,
            COUNT(pi.name) AS invoice_count,
            SUM(pi.grand_total) AS total_amount
        FROM `tabPurchase Invoice` pi
        WHERE pi.docstatus = 1
    """

    values = []

    if filters.get("company"):
        sql += " AND pi.company = %s"
        values.append(filters.get("company"))

    if filters.get("year"):
        sql += " AND YEAR(pi.posting_date) = %s"
        values.append(int(filters.get("year")))

    sql += " GROUP BY pi.supplier ORDER BY pi.supplier"

    return frappe.db.sql(sql, values, as_dict=True)


# ============ MONTH-WISE BREAKUP POPUP ============ #

@frappe.whitelist()
def get_month_breakup(supplier, company=None, year=None):
    sql = """
        SELECT 
            DATE_FORMAT(posting_date, '%%b') AS month,
            SUM(grand_total) AS amount
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1 AND supplier = %s
    """

    values = [supplier]

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

    html = "<h4>Month-wise Purchase</h4>"
    html += "<table class='table table-bordered'>"
    html += "<tr><th>Month</th><th>Amount</th></tr>"

    for d in data:
        html += f"<tr><td>{d.month}</td><td>{frappe.utils.fmt_money(d.amount)}</td></tr>"

    html += "</table>"
    return html
