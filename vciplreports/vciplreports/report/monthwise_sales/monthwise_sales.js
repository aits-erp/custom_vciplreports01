frappe.query_reports["Monthwise Sales"] = {

    onload: function(report) {

        // ---- INVOICE COUNT CLICK ----
        report.page.on("click", ".inv-click", function () {
            let customer = $(this).data("customer");

            frappe.set_route("List", "Sales Invoice", {
                customer: customer,
                docstatus: 1
            });
        });

        // ---- TOTAL AMOUNT CLICK ----
        report.page.on("click", ".amt-click", function () {
            let customer = $(this).data("customer");

            frappe.call({
                method: "your_app.your_app.report.monthwise_sales.monthwise_sales.get_month_breakup",
                args: {
                    customer: customer,
                    company: frappe.query_report.get_filter_value("company"),
                    year: frappe.query_report.get_filter_value("year")
                },
                callback: function (r) {
                    frappe.msgprint({
                        title: "Monthwise Sales - " + customer,
                        message: r.message,
                        wide: true
                    });
                }
            });
        });
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // CLICKABLE INVOICE COUNT
        if (column.fieldname === "invoice_count" && data.customer) {
            return `<a class="inv-click" data-customer="${data.customer}" style="cursor:pointer; color:#007bff;">
                        ${value}
                    </a>`;
        }

        // CLICKABLE TOTAL AMOUNT
        if (column.fieldname === "total_amount" && data.customer) {
            return `<a class="amt-click" data-customer="${data.customer}" style="cursor:pointer; color:#c62828;">
                        ${value}
                    </a>`;
        }

        return value;
    }
};
