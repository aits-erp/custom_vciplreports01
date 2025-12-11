frappe.pages['report-dashboard'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Report Dashboard',
        single_column: true
    });

    $(frappe.render_template("report_dashboard", {})).appendTo(page.body);

    // Click Routing
    $(".report-card").on("click", function () {
        let report_name = $(this).data("report");

        // Small click bounce animation
        $(this).css("transform", "scale(0.95)");

        setTimeout(() => {
            $(this).css("transform", "scale(1)");
            frappe.set_route("query-report", report_name);
        }, 120);
    });
};
