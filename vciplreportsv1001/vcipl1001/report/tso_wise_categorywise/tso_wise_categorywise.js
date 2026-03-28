// frappe.query_reports["TSO WISE CATEGORYWISE"] = {

//     filters: [

//         {
//             fieldname: "from_date",
//             label: "From Date",
//             fieldtype: "Date",
//             default: frappe.datetime.month_start()
//         },
//         {
//             fieldname: "to_date",
//             label: "To Date",
//             fieldtype: "Date",
//             default: frappe.datetime.month_end()
//         },

//         // 🔥 HEAD SALES PERSON (NEW)
//         {
//             fieldname: "parent_sales_person",
//             label: "Head Sales Person",
//             fieldtype: "Link",
//             options: "Sales Person"
//         },

//         // 🔥 TSO
//         {
//             fieldname: "tso",
//             label: "TSO",
//             fieldtype: "Link",
//             options: "Sales Person"
//         },

//         // 🔥 CUSTOMER
//         {
//             fieldname: "customer",
//             label: "Customer",
//             fieldtype: "Link",
//             options: "Customer"
//         },

//         // 🔥 CUSTOMER GROUP
//         {
//             fieldname: "customer_group",
//             label: "Customer Group",
//             fieldtype: "Link",
//             options: "Customer Group",
//             default: "Debtors Distributors"
//         },

//         // 🔥 CATEGORY
//         {
//             fieldname: "item_group",
//             label: "Category",
//             fieldtype: "Link",
//             options: "Item Group"
//         },

//         // 🔥 COMPANY
//         {
//             fieldname: "company",
//             label: "Company",
//             fieldtype: "Link",
//             options: "Company",
//             default: frappe.defaults.get_user_default("Company"),
//             reqd: 1
//         }
//     ]
// };
frappe.query_reports["TSO WISE CATEGORYWISE"] = {
    filters: [

        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.month_end()
        },

        {
            fieldname: "parent_sales_person",
            label: "Head Sales Person",
            fieldtype: "Link",
            options: "Sales Person"
        },

        {
            fieldname: "tso",
            label: "TSO",
            fieldtype: "Link",
            options: "Sales Person"
        },

        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },

        {
            fieldname: "customer_group",
            label: "Customer Group",
            fieldtype: "Link",
            options: "Customer Group",
            default: "Debtors Distributors"
        },

        {
            fieldname: "region",
            label: "Sales Region",
            fieldtype: "Data"
        },

        {
            fieldname: "item_group",
            label: "Category",
            fieldtype: "MultiSelectList",
            get_data: function(txt) {
                return frappe.db.get_link_options("Item Group", txt);
            }
        },

        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        }
    ]
};