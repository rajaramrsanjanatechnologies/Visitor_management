frappe.ui.form.on("Visitor", {
  refresh(frm) {
    if (frm.is_new()) {
      return;
    }

    frm.add_custom_button(__("Print Visitor Slip"), () => {
      const url =
        "/printview?doctype=Visitor&name=" +
        encodeURIComponent(frm.doc.name) +
        "&format=Visitor%20Slip&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en";
      window.open(url, "_blank");
    });

    frm.add_custom_button(__("Send WhatsApp"), () => open_visitor_whatsapp(frm, false));
    frm.add_custom_button(__("Overdue WhatsApp"), () => open_visitor_whatsapp(frm, true));

    if (frm.doc.status !== "Exited") {
      frm.add_custom_button(__("Mark Exit"), () => {
        frappe.confirm(__("Mark this visitor as exited now?"), () => {
          frappe.call({
            method: "visitor_management.visitor_management.doctype.visitor.visitor.mark_exit",
            args: { visitor: frm.doc.name },
            freeze: true,
            freeze_message: __("Marking visitor exit..."),
            callback() {
              frm.reload_doc();
            },
          });
        });
      });
    }

    if (frm.doc.status === "Arrived") {
      frm.add_custom_button(__("Record Action"), () => {
        frappe.prompt(
          [{ fieldname: "action_taken", label: __("Action Taken"), fieldtype: "Small Text", reqd: 1 }],
          (values) => {
            frappe.call({
              method: "visitor_management.visitor_management.doctype.visitor.visitor.record_action",
              args: { visitor: frm.doc.name, action_taken: values.action_taken },
              freeze: true,
              callback() {
                frm.reload_doc();
              },
            });
          },
          __("Record Action"),
          __("Update")
        );
      });
    }
  },

  assigned_employee(frm) {
    if (!frm.doc.assigned_employee) {
      return;
    }
    frappe.db.get_doc("Employee", frm.doc.assigned_employee).then((emp) => {
      frm.set_value("employee_name", emp.employee_name || "");
      frm.set_value("employee_email", emp.company_email || emp.prefered_email || emp.personal_email || "");
      frm.set_value("employee_whatsapp", emp.cell_number || "");
      frm.set_value("reporting_manager", emp.reports_to || "");
      if (emp.reports_to) {
        frappe.db.get_doc("Employee", emp.reports_to).then((mgr) => {
          frm.set_value("reporting_manager_email", mgr.company_email || mgr.prefered_email || mgr.personal_email || "");
        });
      }
    });
  },

  after_save(frm) {
    if (frm.doc.status === "Arrived" && frm.doc.employee_whatsapp && !frm.doc.whatsapp_sent) {
      open_visitor_whatsapp(frm, false);
      frappe.db.set_value("Visitor", frm.doc.name, "whatsapp_sent", 1).then(() => frm.reload_doc());
    }
  },
});

function clean_phone(no) {
  no = (no || "").replace(/[^0-9]/g, "");
  if (no.length === 10) {
    no = "91" + no;
  }
  return no;
}

function open_visitor_whatsapp(frm, overdue) {
  const phone = clean_phone(frm.doc.employee_whatsapp);
  if (!phone) {
    frappe.msgprint(__("Employee WhatsApp/mobile number is missing."));
    return;
  }

  const msg = overdue
    ? "Reminder: Visitor " +
      (frm.doc.visitor_name || "") +
      " has not exited. Slip " +
      frm.doc.name +
      ". Arrival: " +
      (frm.doc.arrival_time || "") +
      ". Please confirm status."
    : "Visitor arrived: " +
      (frm.doc.visitor_name || "") +
      "\nMobile: " +
      (frm.doc.contact_number || "") +
      "\nCompany: " +
      (frm.doc.company || "-") +
      "\nPurpose: " +
      (frm.doc.purpose || "-") +
      "\nSlip: " +
      frm.doc.name;

  window.open("https://wa.me/" + phone + "?text=" + encodeURIComponent(msg), "_blank");
}

