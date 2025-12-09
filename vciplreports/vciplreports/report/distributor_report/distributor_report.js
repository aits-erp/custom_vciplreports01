frappe.query_reports["Distributor Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 0
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 0
        },
        {
            fieldname: "asm",
            label: __("ASM"),
            fieldtype: "Link",
            options: "Sales Person",
            reqd: 0
        },
        {
            fieldname: "rsm",
            label: __("RSM"),
            fieldtype: "Link",
            options: "Sales Person",
            reqd: 0
        }
    ]
};
