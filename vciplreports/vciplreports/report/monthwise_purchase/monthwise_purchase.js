frappe.query_reports["Monthwise Purchase"] = {
    // optional: define client-side default filters here if you want
    onload: function(report) {
        report.page.set_title("Monthwise Purchase");
    },

    // formatter to make month clickable for drill-down
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "month" && data && data.month) {
            // month label is like "Jan-2025"
            var parts = data.month.split('-');
            var monthName = parts[0];
            var year = parts[1];

            var monthMap = {
                Jan: "01", Feb: "02", Mar: "03", Apr: "04",
                May: "05", Jun: "06", Jul: "07", Aug: "08",
                Sep: "09", Oct: "10", Nov: "11", Dec: "12"
            };

            var mm = monthMap[monthName] || "01";
            var start = year + "-" + mm + "-01";
            // get end day for month (simple way: new Date(year, mm, 0))
            var endDay = new Date(year, parseInt(mm, 10), 0).getDate();
            var end = year + "-" + mm + "-" + (endDay < 10 ? "0" + endDay : endDay);

            var href = `<a href="#" class="month-link">${data.month}</a>`;

            // attach click handler (delegated)
            setTimeout(function() {
                $(".month-link").off("click").on("click", function(e) {
                    e.preventDefault();
                    // open Purchase Invoice list filtered by posting_date range and (optionally) company
                    frappe.set_route("List", "Purchase Invoice", {
                        "posting_date": ["between", start, end]
                    });
                });
            }, 0);

            return href;
        }

        return value;
    }
};
