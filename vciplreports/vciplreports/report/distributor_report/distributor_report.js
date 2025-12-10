frappe.query_reports["Distributor Report"] = {

    // FORMATTER (Makes Invoice Count Clickable)
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Make invoice count clickable (opens popup)
        if (column.fieldname === "invoice_count" && data.invoices) {
            return `<a style="cursor:pointer; color:#1674E0; font-weight:bold;"
                onclick='frappe.query_reports["Distributor Report"].show_invoice_popup(${data.invoices})'>
                ${value}
            </a>`;
        }

        return value;
    },

    // POPUP FUNCTION - Shows list of invoices for that customer
    show_invoice_popup(invoices) {
        let html = `
            <div style="max-height:500px; overflow-y:auto;">
            <table class="table table-bordered" style="font-size:13px;">
                <thead>
                    <tr>
                        <th>Invoice No</th>
                        <th>Posting Date</th>
                        <th>Outstanding</th>
                        <th>Overdue</th>
                    </tr>
                </thead>
                <tbody>
        `;

        invoices.forEach(inv => {
            html += `
                <tr>
                    <td>
                        <a href="/app/sales-invoice/${inv.invoice}"
                           target="_blank"
                           style="color:#1674E0; font-weight:bold;">
                            ${inv.invoice}
                        </a>
                    </td>
                    <td>${inv.posting_date}</td>
                    <td>${format_currency(inv.outstanding)}</td>
                    <td>${format_currency(inv.overdue)}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
            </div>
        `;

        frappe.msgprint({
            title: __("Invoice Details"),
            indicator: "blue",
            message: html,
            wide: true
        });
    }
};
