frappe.query_reports["Monthwise Purchase"] = {
    onload: function(report) {

        // Listen for clicks on supplier links
        $(document).on("click", ".supplier-link", function(e) {
            e.preventDefault();

            let supplier = $(this).data("supplier");
            let filters = report.get_values();

            frappe.call({
                method: "your_app.your_module.monthwise_purchase.get_month_breakup",
                args: {
                    supplier: supplier,
                    company: filters.company,
                    year: filters.year
                },
                callback: function(r) {
                    frappe.msgprint({
                        title: "Month-wise Purchase for: " + supplier,
                        indicator: "blue",
                        message: r.message
                    });
                }
            });
        });

    }
};
