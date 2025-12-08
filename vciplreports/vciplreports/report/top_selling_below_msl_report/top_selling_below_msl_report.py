import frappe

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link",
         "options": "Item", "width": 150},

        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 200},

        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Link",
         "options": "Item Group", "width": 150},

        {"label": "Total Sales Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 150},

        {"label": "Total Sold Qty", "fieldname": "total_qty", "fieldtype": "Float", "width": 120},

        {"label": "Total Stock Qty", "fieldname": "total_stock_qty", "fieldtype": "Float", "width": 140},

        {"label": "Minimum Stock Level", "fieldname": "min_stock_level", "fieldtype": "Float", "width": 140},

        {"label": "Shortage Qty", "fieldname": "shortage_qty", "fieldtype": "Float", "width": 120},

        # drill down link
        {"label": "Warehouses", "fieldname": "details", "fieldtype": "Data", "width": 120},
    ]

    data = get_data(filters)
    return columns, data


def get_data(filters):

    params = {"docstatus": 1}
    conditions = " AND si.docstatus = %(docstatus)s"

    # --------------------------------------
    # SALES QUERY
    # --------------------------------------
    sales_query = f"""
        SELECT
            sii.item_code,
            i.item_name,
            i.item_group,
            SUM(sii.amount) AS total_amount,
            SUM(sii.qty) AS total_qty,
            COALESCE(i.min_order_qty, 0) AS min_stock_level
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        JOIN `tabItem` i ON i.name = sii.item_code
        WHERE 1 = 1
        {conditions}
        GROUP BY sii.item_code, i.item_name, i.item_group, i.min_order_qty
        ORDER BY total_amount DESC
        LIMIT 100
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

    # Always include WIP warehouse with qty = 0 if not present
    for item in item_codes:
        warehouse_map.setdefault(item, {})
        warehouse_map[item].setdefault(WIP_WAREHOUSE, 0)

    # --------------------------------------
    # FINAL DATA MERGE
    # --------------------------------------
    for r in rows:
        item_code = r.item_code

        r["total_stock_qty"] = total_stock.get(item_code, 0)

        min_level = r.get("min_stock_level") or 0
        shortage = min_level - r["total_stock_qty"]
        r["shortage_qty"] = shortage if shortage > 0 else 0

        r["details"] = "View Warehouses"

    return rows
