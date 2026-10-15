import frappe


SECURITY_EMAIL = "security@sanjanatechnologies.com"
SECURITY_PASSWORD = "Aqj@Visitor#2026"
MANAGEMENT_EMAIL = "erpadmin@sanjanatechnologies.com"


def after_install():
    setup(reset_security_password=True)


def after_migrate():
    setup(reset_security_password=False)


def setup(reset_security_password=False):
    ensure_roles()
    ensure_security_user(reset_security_password=reset_security_password)
    ensure_employee_select_permission()
    ensure_workflow_masters()
    ensure_workflow()
    ensure_email_template()
    ensure_print_format()
    disable_duplicate_notification()
    frappe.db.commit()


def ensure_roles():
    for role_name in ("Security", "Receptionist"):
        if frappe.db.exists("Role", role_name):
            role = frappe.get_doc("Role", role_name)
            role.desk_access = 1
            role.save(ignore_permissions=True)
        else:
            role = frappe.new_doc("Role")
            role.role_name = role_name
            role.desk_access = 1
            role.insert(ignore_permissions=True)


def ensure_security_user(reset_security_password=False):
    if frappe.db.exists("User", SECURITY_EMAIL):
        user = frappe.get_doc("User", SECURITY_EMAIL)
    else:
        user = frappe.new_doc("User")
        user.email = SECURITY_EMAIL
        user.first_name = "Security"
        user.last_name = "Desk"
        user.username = "security"
        user.send_welcome_email = 0

    user.enabled = 1
    user.user_type = "System User"
    user.send_welcome_email = 0

    roles = {row.role for row in user.roles}
    for role_name in ("Security", "Receptionist"):
        if role_name not in roles:
            user.append("roles", {"role": role_name})
    user.save(ignore_permissions=True)
    if reset_security_password:
        try:
            from frappe.utils.password import update_password

            update_password(SECURITY_EMAIL, SECURITY_PASSWORD, logout_all_sessions=True)
        except Exception:
            user = frappe.get_doc("User", SECURITY_EMAIL)
            user.new_password = SECURITY_PASSWORD
            user.save(ignore_permissions=True)


def ensure_employee_select_permission():
    if not frappe.db.exists("DocType", "Employee"):
        return

    values = {
        "read": 1,
        "select": 1,
        "write": 0,
        "create": 0,
        "delete": 0,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "report": 0,
        "export": 0,
        "print": 0,
        "email": 0,
    }
    existing = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": "Employee", "role": "Security", "permlevel": 0},
        pluck="name",
    )
    doc = frappe.get_doc("Custom DocPerm", existing[0]) if existing else frappe.new_doc("Custom DocPerm")
    doc.update(
        {
            "parent": "Employee",
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": "Security",
            "permlevel": 0,
            **values,
        }
    )
    doc.save(ignore_permissions=True) if doc.name else doc.insert(ignore_permissions=True)


def ensure_workflow_masters():
    states = {
        "Arrived": "Primary",
        "Action Taken": "Warning",
        "Exited": "Success",
    }
    for state_name, style in states.items():
        if not frappe.db.exists("Workflow State", state_name):
            state = frappe.new_doc("Workflow State")
            state.workflow_state_name = state_name
            state.style = style
            state.insert(ignore_permissions=True)

    if frappe.db.exists("DocType", "Workflow Action Master"):
        for action_name in ("Record Action", "Mark Exit"):
            if not frappe.db.exists("Workflow Action Master", action_name):
                action = frappe.new_doc("Workflow Action Master")
                action.workflow_action_name = action_name
                action.insert(ignore_permissions=True)


def ensure_workflow():
    if frappe.db.exists("Workflow", "Visitor Workflow"):
        workflow = frappe.get_doc("Workflow", "Visitor Workflow")
    else:
        workflow = frappe.new_doc("Workflow")
        workflow.workflow_name = "Visitor Workflow"

    workflow.document_type = "Visitor"
    workflow.workflow_state_field = "status"
    workflow.is_active = 1
    workflow.send_email_alert = 0
    workflow.override_status = 0
    workflow.states = []
    workflow.transitions = []

    for role_name in ("System Manager", "Security", "Receptionist"):
        for state_name in ("Arrived", "Action Taken", "Exited"):
            workflow.append(
                "states",
                {"state": state_name, "doc_status": 0, "allow_edit": role_name},
            )

    for role_name in ("System Manager", "Security", "Receptionist"):
        workflow.append(
            "transitions",
            {
                "state": "Arrived",
                "action": "Record Action",
                "next_state": "Action Taken",
                "allowed": role_name,
                "allow_self_approval": 1,
            },
        )
        workflow.append(
            "transitions",
            {
                "state": "Arrived",
                "action": "Mark Exit",
                "next_state": "Exited",
                "allowed": role_name,
                "allow_self_approval": 1,
            },
        )
        workflow.append(
            "transitions",
            {
                "state": "Action Taken",
                "action": "Mark Exit",
                "next_state": "Exited",
                "allowed": role_name,
                "allow_self_approval": 1,
            },
        )

    workflow.save(ignore_permissions=True) if workflow.name else workflow.insert(ignore_permissions=True)


def ensure_email_template():
    response_html = """
<div style="font-family:Arial,sans-serif;font-size:13px;color:#111;max-width:620px;">
  <h3 style="margin:0 0 6px;text-align:center;">Visitor Arrival</h3>
  <p>Hello {{ doc.employee_name or 'Employee' }},</p>
  <p>A visitor has arrived for you.</p>
  {% if doc.visitor_photo %}
  <p><img src="{{ frappe.utils.get_url(doc.visitor_photo) }}" style="width:120px;height:90px;object-fit:cover;border:1px solid #ddd;"></p>
  {% endif %}
  <table style="border-collapse:collapse;font-size:13px;">
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Name</td><td>{{ doc.visitor_name }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Contact</td><td>{{ doc.contact_number }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Email</td><td>{{ doc.email or '-' }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Company</td><td>{{ doc.company or '-' }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">ID</td><td>{{ doc.aadhar_no or '-' }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Vehicle</td><td>{{ doc.vehicle_no or '-' }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Purpose</td><td>{{ doc.purpose or '-' }}</td></tr>
    <tr><td style="font-weight:bold;padding:3px 12px 3px 0;">Arrival Time</td><td>{{ frappe.utils.format_datetime(doc.arrival_time) }}</td></tr>
  </table>
  <p>Please attend to the visitor and update the action taken in ERPNext.</p>
</div>
"""
    if frappe.db.exists("Email Template", "Visitor Arrival Notification"):
        template = frappe.get_doc("Email Template", "Visitor Arrival Notification")
    else:
        template = frappe.new_doc("Email Template")
        template.email_template_name = "Visitor Arrival Notification"

    template.subject = "Visitor arrived: {{ doc.visitor_name }}"
    if template.meta.has_field("response_html"):
        template.response_html = response_html
    if template.meta.has_field("response"):
        template.response = response_html
    template.use_html = 1
    template.save(ignore_permissions=True) if template.name else template.insert(ignore_permissions=True)


def ensure_print_format():
    html = frappe.get_template("visitor_management/templates/visitor_slip.html").render()
    if frappe.db.exists("Print Format", "Visitor Slip"):
        print_format = frappe.get_doc("Print Format", "Visitor Slip")
    else:
        print_format = frappe.new_doc("Print Format")
        print_format.print_format_name = "Visitor Slip"

    print_format.doc_type = "Visitor"
    print_format.print_format_type = "Jinja"
    print_format.html = html
    print_format.standard = "No"
    print_format.disabled = 0
    print_format.save(ignore_permissions=True) if print_format.name else print_format.insert(ignore_permissions=True)


def disable_duplicate_notification():
    if frappe.db.exists("Notification", "Visitor Arrival Notification"):
        notification = frappe.get_doc("Notification", "Visitor Arrival Notification")
        notification.enabled = 0
        notification.save(ignore_permissions=True)
