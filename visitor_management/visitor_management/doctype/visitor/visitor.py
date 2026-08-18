import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, format_datetime, get_datetime, get_url, now_datetime, today


class Visitor(Document):
    pass


def set_defaults(doc, method=None):
    if not doc.arrival_time:
        doc.arrival_time = now_datetime()
    if not doc.status:
        doc.status = "Arrived"
    if not doc.management_email:
        doc.management_email = "erpadmin@aqjapparels.com"


def validate_visit(doc, method=None):
    set_defaults(doc)
    set_employee_details(doc)

    if doc.status == "Exited" and not doc.exit_time:
        doc.exit_time = now_datetime()

    if doc.exit_time and doc.arrival_time and get_datetime(doc.exit_time) < get_datetime(doc.arrival_time):
        frappe.throw("Exit Time cannot be before Arrival Time.")


def set_employee_details(doc):
    if not doc.assigned_employee:
        return

    employee = frappe.db.get_value(
        "Employee",
        doc.assigned_employee,
        [
            "employee_name",
            "company_email",
            "prefered_email",
            "personal_email",
            "cell_number",
            "reports_to",
        ],
        as_dict=True,
    )
    if not employee:
        return

    doc.employee_name = employee.employee_name
    doc.employee_email = employee.company_email or employee.prefered_email or employee.personal_email or ""
    doc.employee_whatsapp = employee.cell_number or ""
    doc.reporting_manager = employee.reports_to or ""

    if employee.reports_to:
        manager = frappe.db.get_value(
            "Employee",
            employee.reports_to,
            ["company_email", "prefered_email", "personal_email"],
            as_dict=True,
        )
        if manager:
            doc.reporting_manager_email = (
                manager.company_email or manager.prefered_email or manager.personal_email or ""
            )


def notify_employee_on_arrival(doc, method=None):
    if doc.status != "Arrived" or doc.notification_sent:
        return

    set_employee_details(doc)
    recipients = get_employee_recipients(doc)
    if not recipients:
        frappe.throw("Assigned Employee and Reporting Manager do not have an email address.")

    subject = f"Visitor arrived: {doc.visitor_name}"
    message = build_arrival_email(doc)
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        reference_doctype=doc.doctype,
        reference_name=doc.name,
        now=False,
    )
    frappe.db.set_value(doc.doctype, doc.name, "notification_sent", 1, update_modified=False)


def get_employee_recipients(doc):
    if doc.employee_email:
        return [doc.employee_email]
    if doc.reporting_manager_email:
        return [doc.reporting_manager_email]
    return []


def build_arrival_email(doc):
    photo_html = ""
    if doc.visitor_photo:
        photo_html = (
            f"<p><img src='{get_url(doc.visitor_photo)}' "
            "style='width:120px;height:90px;object-fit:cover;border:1px solid #ddd;'></p>"
        )

    rows = [
        ("Name", doc.visitor_name),
        ("Contact", doc.contact_number),
        ("Email", doc.email or "-"),
        ("Company", doc.company or "-"),
        ("ID", doc.aadhar_no or "-"),
        ("Vehicle", doc.vehicle_no or "-"),
        ("Purpose", doc.purpose or "-"),
        ("Arrival Time", format_datetime(doc.arrival_time)),
    ]
    row_html = "".join(
        "<tr><td style='font-weight:bold;padding:3px 12px 3px 0;'>{}</td><td>{}</td></tr>".format(
            frappe.utils.escape_html(label), frappe.utils.escape_html(value or "")
        )
        for label, value in rows
    )
    return f"""
<div style='font-family:Arial,sans-serif;font-size:13px;color:#111;max-width:620px;'>
  <h3 style='text-align:center;margin:0 0 8px;'>Visitor Arrival</h3>
  <p>Hello {frappe.utils.escape_html(doc.employee_name or "Employee")},</p>
  <p>A visitor has arrived for you.</p>
  {photo_html}
  <table style='border-collapse:collapse;font-size:13px;'>{row_html}</table>
  <p>Please attend to the visitor and update the action taken in ERPNext.</p>
</div>
"""


@frappe.whitelist()
def mark_exit(visitor):
    doc = frappe.get_doc("Visitor", visitor)
    doc.check_permission("write")
    if doc.status != "Exited":
        doc.status = "Exited"
        doc.exit_time = now_datetime()
        doc.save()
    return {"status": doc.status, "exit_time": doc.exit_time}


@frappe.whitelist()
def record_action(visitor, action_taken):
    doc = frappe.get_doc("Visitor", visitor)
    doc.check_permission("write")
    doc.action_taken = action_taken
    doc.status = "Action Taken"
    doc.save()
    return {"status": doc.status, "action_taken": doc.action_taken}


def send_overdue_visitor_alerts():
    now_dt = now_datetime()
    today_date = today()
    visitors = frappe.get_all(
        "Visitor",
        filters={"status": ["in", ["Arrived", "Action Taken"]], "exit_time": ["is", "not set"]},
        fields=[
            "name",
            "visitor_name",
            "company",
            "purpose",
            "assigned_employee",
            "employee_name",
            "employee_email",
            "employee_whatsapp",
            "reporting_manager_email",
            "management_email",
            "arrival_time",
        ],
        limit_page_length=500,
    )

    overdue = []
    for visitor in visitors:
        if not visitor.arrival_time:
            continue
        after_six_hours = now_dt >= add_to_date(visitor.arrival_time, hours=6)
        after_730_same_day = (
            str(visitor.arrival_time)[0:10] == today_date and int(now_dt.strftime("%H%M")) >= 1930
        )
        if after_six_hours or after_730_same_day:
            overdue.append(visitor)

    if not overdue:
        return

    recipients = set()
    for visitor in overdue:
        recipients.add(visitor.employee_email or visitor.reporting_manager_email or "")
        recipients.add(visitor.management_email or "")
    recipients.discard("")

    if recipients:
        frappe.sendmail(
            recipients=list(recipients),
            subject="Visitor Overdue / Not Exited Alert",
            message=build_overdue_email(overdue),
            now=False,
        )

    for visitor in overdue:
        frappe.db.set_value("Visitor", visitor.name, "overdue_alert_sent", 1, update_modified=False)


def build_overdue_email(visitors):
    rows = ""
    for visitor in visitors:
        rows += """
<tr>
  <td>{name}</td><td>{visitor}</td><td>{company}</td><td>{employee}</td><td>{arrival}</td><td>{purpose}</td>
</tr>
""".format(
            name=frappe.utils.escape_html(visitor.name),
            visitor=frappe.utils.escape_html(visitor.visitor_name or ""),
            company=frappe.utils.escape_html(visitor.company or ""),
            employee=frappe.utils.escape_html(visitor.employee_name or visitor.assigned_employee or ""),
            arrival=frappe.utils.escape_html(format_datetime(visitor.arrival_time)),
            purpose=frappe.utils.escape_html(visitor.purpose or ""),
        )
    return f"""
<p>The following visitors have not exited.</p>
<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;font-size:12px;">
  <tr><th>Slip</th><th>Visitor</th><th>Company</th><th>Employee</th><th>Arrival</th><th>Purpose</th></tr>
  {rows}
</table>
"""

