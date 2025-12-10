frappe.query_reports["Sales Analytic Report"] = {
    onload: function (report) {
        // Enable tree structure visually
        report.tree_report = true;
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (!data) return value;

        let indent = data.indent || 0;
        let space = "";

        // Add indentation
        for (let i = 0; i < indent; i++) {
            space += `<span style="padding-left: 20px;"></span>`;
        }

        // Add expand/collapse arrow only for groups & customers
        if (column.fieldname === "entity") {
            if (indent < 2) {
                // Clickable toggle arrow
                let icon = data._expanded ? "▼" : "▶";

                value = `
                    <span class="tree-toggle" 
                        data-name="${data.entity}"
                        data-indent="${indent}"
                        style="cursor:pointer; font-weight:bold;">
                        ${icon}
                    </span> ${space} ${value}
                `;
            } else {
                // Invoice level – bullet icon only
                value = `${space} ${value}`;
            }
        }

        return value;
    },

    after_datatable_render: function (report) {
        const dt = report.datatable;
        if (!dt) return;

        // Add toggle click listeners
        $(report.page.wrapper)
            .find(".tree-toggle")
            .off("click")
            .on("click", function () {
                let entity = $(this).data("name");
                let indent = $(this).data("indent");

                toggle_rows(report, entity, indent);
            });
    }
};


// -------------------------------------------------------------
// DRILL-DOWN LOGIC
// -------------------------------------------------------------
function toggle_rows(report, entity, indent) {
    let rows = report.data;
    let updated = [];

    let expand_mode = true;

    // Determine current mode (expand or collapse)
    for (let r of rows) {
        if (r.entity === entity && r._expanded) {
            expand_mode = false;
            break;
        }
    }

    for (let r of rows) {

        // If this is the clicked row, toggle its _expanded flag
        if (r.entity === entity) {
            r._expanded = expand_mode;
            updated.push(r);
            continue;
        }

        // If collapsing → hide all children
        if (!expand_mode) {
            if (r.parent_node === entity || r.indent > indent) {
                r._hidden = true;
            }
        }

        // If expanding → show only immediate children
        if (expand_mode) {
            if (r.parent_node === entity) {
                r._hidden = false;

                // collapse their children initially
                r._expanded = false;
            }
        }

        updated.push(r);
    }

    report.datatable.refresh(updated);
}
