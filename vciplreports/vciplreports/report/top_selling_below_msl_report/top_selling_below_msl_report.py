import frappe
from datetime import date


def execute(filters=None):
    filters = filters or {}

    # ---- FINANCIAL YEAR RANGE LOGIC ----
    year = int(filters.get("year")) if filters.get("year") else None

    if year:
        # Example: 2024 → range 01-04-2024 to 31-03-2025
        from_date = date(year, 4, 1)
        to_date = date(year + 1, 3, 31)
    else:
        # default: auto-detect FY based on today
        today = date.today()
        fy_year = today.year if today.month > 3 else today.year - 1
        from_date = date(fy_year, 4, 1)
        to_date = date(fy_year + 1, 3, 31)

    filters["from_date"] = from_date
    filters["to_date"] = to_date

    return get_columns(), get_data(filters)


# -------------------- COLUMNS -------------------- #
def get_columns():
    return [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link",
         "options": "Item", "width": 150},

        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},

        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link",
         "options": "Item Group", "width": 150},

        {"label": "Total Sales Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 150},

        {"label": "Total Sold Qty", "fieldname": "total_qty", "fieldtype": "Float", "width": 120},

        {"label": "Total Stock Qty", "fieldname": "total_stock_qty", "fieldtype": "Float", "width": 140},

        {"label": "Minimum Stock Level (Safety Stock)", "fieldname": "min_stock_level", "fieldtype": "Float", "width": 160},

        {"label": "Shortage Qty", "fieldname": "shortage_qty", "fieldtype": "Float", "width": 120},

        {"label": "Warehouses", "fieldname": "details", "fieldtype": "Data", "width": 120},
    ]


# -------------------- FETCH DATA -------------------- #
def get_data(filters):

    params = {
        "docstatus": 1,
        "from_date": filters["from_date"],
        "to_date": filters["to_date"],
    }

    # --------------------------------------
    # SALES QUERY WITH SAFETY STOCK
    # --------------------------------------
    sales_query = """
        SELECT
            sii.item_code,
            i.item_name,
            i.item_group,
            SUM(sii.amount) AS total_amount,
            SUM(sii.qty) AS total_qty,
            COALESCE(i.safety_stock, 0) AS min_stock_level
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        JOIN `tabItem` i ON i.name = sii.item_code
        WHERE 1 = 1
            AND si.docstatus = %(docstatus)s
            AND si.posting_date >= %(from_date)s
            AND si.posting_date <= %(to_date)s
        GROUP BY sii.item_code, i.item_name, i.item_group, i.safety_stock
        ORDER BY total_amount DESC
        LIMIT 200
    """

    rows = frappe.db.sql(sales_query, params, as_dict=True)

    if not rows:
        return []

    item_codes = [r.item_code for r in rows]

    # --------------------------------------
    # FETCH STOCK FROM BIN
    # --------------------------------------
    bins = frappe.get_all(
        "Bin",
        filters={"item_code": ["in", item_codes]},
        fields=["item_code", "warehouse", "actual_qty"]
    )

    WIP_WAREHOUSE = "Work In Progress - VCIPL"

    total_stock = {}
    warehouse_map = {}

    for b in bins:
        total_stock[b.item_code] = total_stock.get(b.item_code, 0) + b.actual_qty
        warehouse_map.setdefault(b.item_code, {})
        warehouse_map[b.item_code][b.warehouse] = b.actual_qty

    # ensure WIP warehouse exists even if qty = 0
    for item in item_codes:
        warehouse_map.setdefault(item, {})
        warehouse_map[item].setdefault(WIP_WAREHOUSE, 0)

    # --------------------------------------
    # FINAL MERGE
    # --------------------------------------
    for r in rows:
        item_code = r.item_code

        # total stock qty
        r["total_stock_qty"] = total_stock.get(item_code, 0)

        # MSL = safety_stock
        msl = r.get("min_stock_level") or 0

        # shortage qty
        shortage = msl - r["total_stock_qty"]
        r["shortage_qty"] = shortage if shortage > 0 else 0

        # drill down
        r["details"] = "View Warehouses"

    return rows
