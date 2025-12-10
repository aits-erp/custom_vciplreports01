import frappe
from frappe.utils import getdate
from calendar import monthrange

def execute(filters=None):
    filters = filters or {}
    year = cint(filters.get("year")) if filters.get("year") else None
    company = filters.get("company")
    monthly_target = flt(filters.get("monthly_target")) if filters.get("monthly_target") else 0

    rows = get_data(year=year, company=company, target=monthly_target)

    # compute logic: MoM, cumulative, YoY, % target achieved
    processed = []
    prev = None
    cumulative = 0.0

    # prepare last year data for YoY comparison
    yoy_map = get_last_year_map(year, company)

    for r in rows:
        total = r.get("total") or 0.0
        qty = r.get("qty") or 0
        invoice_count = r.get("invoice_count") or 0

        cumulative += total

        # MoM Growth
        growth = None
        if prev is not None and prev > 0:
            growth = round(((total - prev) / prev) * 100, 2)

        # YoY Growth
        last_year_total = yoy_map.get(r.get("mn"), 0)
        yoy_growth = None
        if last_year_total and last_year_total > 0:
            yoy_growth = round(((total - last_year_total) / last_year_total) * 100, 2)

        # Target Achievement
        target_achievement = None
        if monthly_target > 0:
            target_achievement = round((total / monthly_target) * 100, 2)

        processed.append({
            "month": r.get("month"),
            "year": r.get("yr"),
            "month_no": r.get("mn"),
            "total": total,
            "qty": qty,
            "invoice_count": invoice_count,
            "growth": growth,
            "yoy_growth": yoy_growth,
            "cumulative": cumulative,
            "target_achievement": target_achievement
        })

        prev = total

    chart = get_chart_data(processed, yoy_map)
    columns = get_columns()
    summary = get_summary(processed)

    return columns, processed, summary, chart


def cint(v, default=0):
    try:
        return int(v)
    except:
        return default


def flt(v, default=0.0):
    try:
        return float(v)
    except:
        return default


# -----------------------------------------------------------
# COLUMNS
# -----------------------------------------------------------

def get_columns():
    return [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
        {"label": "Total Sales", "fieldname": "total", "fieldtype": "Currency", "width": 140},
        {"label": "Qty Sold", "fieldname": "qty", "fieldtype": "Float", "width": 110},
        {"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int", "width": 100},
        {"label": "MoM Growth %", "fieldname": "growth", "fieldtype": "Percent", "width": 130},
        {"label": "YoY Growth %", "fieldname": "yoy_growth", "fieldtype": "Percent", "width": 130},
        {"label": "Cumulative Sales", "fieldname": "cumulative", "fieldtype": "Currency", "width": 150},
        {"label": "% Target Achieved", "fieldname": "target_achievement", "fieldtype": "Percent", "width": 150},
    ]


# -----------------------------------------------------------
# MAIN DATA FETCH
# -----------------------------------------------------------

def get_data(year=None, company=None, target=0):
    conditions = ["si.docstatus = 1"]
    params = []

    if year:
        conditions.append("YEAR(si.posting_date) = %s")
        params.append(year)

    if company:
        conditions.append("si.company = %s")
        params.append(company)

    where = " AND ".join(conditions)

    sql = f"""
        SELECT
            DATE_FORMAT(si.posting_date, '%%b-%%Y') AS month,
            YEAR(si.posting_date) AS yr,
            MONTH(si.posting_date) AS mn,
            SUM(si.base_grand_total) AS total,
            SUM(sii.qty) AS qty,
            COUNT(DISTINCT si.name) AS invoice_count
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE {where}
        GROUP BY YEAR(si.posting_date), MONTH(si.posting_date)
        ORDER BY YEAR(si.posting_date), MONTH(si.posting_date)
    """

    return frappe.db.sql(sql, tuple(params), as_dict=True)



# -----------------------------------------------------------
# YOY SUPPORTING DATA
# -----------------------------------------------------------

def get_last_year_map(current_year, company):
    """Returns dictionary: {month_no: total_of_last_year_month}"""
    if not current_year:
        return {}

    sql = """
        SELECT MONTH(posting_date) AS mn, SUM(base_grand_total) AS total
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND YEAR(posting_date) = %s
          AND company = %s
        GROUP BY MONTH(posting_date)
    """

    rows = frappe.db.sql(sql, (current_year - 1, company), as_dict=True)
    return {r["mn"]: r["total"] for r in rows}


# -----------------------------------------------------------
# CHART DATA
# -----------------------------------------------------------

def get_chart_data(rows, yoy_map):
    labels = [r["month"] for r in rows]
    values = [r["total"] for r in rows]
    cumulative = [r["cumulative"] for r in rows]
    yoy_values = [yoy_map.get(r["month_no"], 0) for r in rows]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Sales Amount", "type": "bar", "values": values},
                {"name": "Cumulative", "type": "line", "values": cumulative},
                {"name": "Last Year Same Month", "type": "line", "values": yoy_values}
            ]
        },
        "type": "bar",
        "height": 380
    }


# -----------------------------------------------------------
# SUMMARY CARDS
# -----------------------------------------------------------

def get_summary(rows):
    total = sum([r["total"] for r in rows]) if rows else 0.0
    avg = round(total / len(rows), 2) if rows else 0.0

    best = None
    if rows:
        best_row = max(rows, key=lambda x: x["total"])
        best = f"{best_row['month']} ({best_row['total']})"

    last_growth = rows[-1]["growth"] if rows and rows[-1].get("growth") else None
    yoy_latest = rows[-1]["yoy_growth"] if rows and rows[-1].get("yoy_growth") else None

    summary = [
        {"label": "Total Sales", "value": total, "indicator": "green"},
        {"label": "Average Monthly Sales", "value": avg},
        {"label": "Best Month", "value": best or "N/A"},
        {"label": "Latest MoM Growth", "value": f"{last_growth} %" if last_growth is not None else "N/A"},
        {"label": "Latest YoY Growth", "value": f"{yoy_latest} %" if yoy_latest is not None else "N/A"},
    ]
    return summary
