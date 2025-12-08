frappe.query_reports["Top selling below MSL report"] = {
    onload: function(report) {
        report.set_filter_value("custom_item_type", "Finished Goods");   // default filter
    },

    filters: [
        {
            fieldname: "custom_item_type",
            label: __("Item Type"),
            fieldtype: "Data",
            default: "Finished Goods",
            reqd: 0
        }
    ],

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Add clickable drill-down link
        if (column.fieldname === "details" && data.item_code) {
            value = `<a href="#" data-item="${data.item_code}" class="show-warehouses">
                        View Warehouses
                     </a>`;
        }

        return value;
    }
};


// ---------------------------------------------------------
// DRILL DOWN: SHOW WAREHOUSE STOCK IN POPUP
// ---------------------------------------------------------
$(document).on("click", ".show-warehouses", function(e) {
    e.preventDefault();

    const item_code = $(this).data("item");

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Bin",
            filters: { "item_code": item_code },
            fields: ["warehouse", "actual_qty"]
        },
        callback: function(r) {
            let rows = r.message || [];

            let html = "<table class='table table-bordered'>";
            html += "<tr><th>Warehouse</th><th>Stock Qty</th></tr>";

            rows.forEach(row => {
                html += `<tr><td>${row.warehouse}</td><td>${row.actual_qty}</td></tr>`;
            });

            html += "</table>";

            frappe.msgprint({
                title: "Warehouse Stock for: " + item_code,
                message: html,
                wide: true
            });
        }
    });
});
