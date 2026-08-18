app_name = "visitor_management"
app_title = "Visitor Management"
app_publisher = "Sanjana Technologies"
app_description = "Visitor management workflow for ERPNext"
app_email = "erpadmin@aqjapparels.com"
app_license = "MIT"

after_install = "visitor_management.install.after_install"
after_migrate = "visitor_management.install.after_migrate"

doc_events = {
    "Visitor": {
        "before_insert": "visitor_management.visitor_management.doctype.visitor.visitor.set_defaults",
        "validate": "visitor_management.visitor_management.doctype.visitor.visitor.validate_visit",
        "after_insert": "visitor_management.visitor_management.doctype.visitor.visitor.notify_employee_on_arrival",
    }
}

doctype_js = {
    "Visitor": "public/js/visitor.js"
}

scheduler_events = {
    "hourly": [
        "visitor_management.visitor_management.doctype.visitor.visitor.send_overdue_visitor_alerts"
    ]
}

fixtures = [
    {
        "dt": "Print Format",
        "filters": [["name", "=", "Visitor Slip"]],
    },
    {
        "dt": "Email Template",
        "filters": [["name", "=", "Visitor Arrival Notification"]],
    },
]

