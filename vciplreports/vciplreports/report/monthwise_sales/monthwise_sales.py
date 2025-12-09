import frappe
from frappe.utils import getdate
from calendar import monthrange

def execute(filters=None):
    filters = filters or {}
    year = cint(filters.get("year")) if filters.get("year") else None
    company = filters.get("company")

    rows = get_data(year=year, company=company)
    # compute growth % and cumulative
    processed = []
    prev = None
    cumulative = 0.0
    for r in rows:
        total = r.get("total") or 0.0
        cumulative += total
        growth = None
        if prev is not None and prev > 0:
            growth = round(((total - prev) / prev) * 100, 2)
        processed.append({
            "month": r.get("month"),
            "year": r.get("yr"),
            "month_no": r.get("mn"),
            "total": total,
            "growth": growth,
            "cumulative": cumulative
        })
        prev = total

    chart = get_chart_data(processed)
    columns = get_columns()
    summary = get_summary(processed)

    return columns, processed, summary, chart


def cint(v, default=0):
    try:
        return int(v)
    except:
        return default


def get_columns():
    return [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 150},
        {"label": "Total Sales", "fieldname": "total", "fieldtype": "Currency", "width": 150},
        {"label": "MoM Growth %", "fieldname": "growth", "fieldtype": "Percent", "width": 120},
        {"label": "Cumulative", "fieldname": "cumulative", "fieldtype": "Currency", "width": 150},
    ]


def get_data(year=None, company=None):
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
            SUM(si.base_grand_total) AS total
        FROM `tabSales Invoice` si
        WHERE {where}
        GROUP BY YEAR(si.posting_date), MONTH(si.posting_date)
        ORDER BY YEAR(si.posting_date), MONTH(si.posting_date)
    """

    return frappe.db.sql(sql, tuple(params), as_dict=True)


def get_chart_data(rows):
    labels = [r["month"] for r in rows]
    values = [r["total"] for r in rows]
    cumulative = [r["cumulative"] for r in rows]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Sales Amount", "values": values},
                {"name": "Cumulative", "values": cumulative}
            ]
        },
        "type": "bar",
        "height": 350
    }


def get_summary(rows):
    total = sum([r["total"] for r in rows]) if rows else 0.0
    avg = round(total / len(rows), 2) if rows else 0.0
    best = None
    if rows:
        best_row = max(rows, key=lambda x: x["total"])
        best = f"{best_row['month']} ({best_row['total']})"

    last_growth = rows[-1]["growth"] if rows and rows[-1].get("growth") is not None else None
    growth_label = f"{last_growth} %" if last_growth is not None else "N/A"

    summary = [
        {"label": "Total Sales", "value": total, "indicator": "green"},
        {"label": "Average / Month", "value": avg},
        {"label": "Best Month", "value": best or "N/A"},
        {"label": "Latest MoM Growth", "value": growth_label, "indicator": "neutral"}
    ]
    return summary
