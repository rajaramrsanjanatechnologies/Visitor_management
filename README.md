# Visitor Management

Frappe/ERPNext custom app for visitor entry, employee notification, WhatsApp prompt, thermal visitor slip printing, action tracking, exit logging, overdue escalation, and Security desk access.

## Install

From your bench folder:

```bash
bench get-app /path/to/visitor_management
bench --site your-site install-app visitor_management
bench --site your-site migrate
bench build
bench restart
```

Security login created by the installer:

- User: `security@aqjapparels.com`
- Temporary password: `Aqj@Visitor#2026`

Change the password after first login.

## Main Features

- Visitor DocType with visitor details, photo, Aadhar/License number, vehicle number, employee details, arrival/exit timing, action taken, and notification flags.
- Automatic employee email on visitor arrival with inline photo.
- Free WhatsApp workflow using WhatsApp Web / `wa.me` pre-filled messages.
- Thermal `Visitor Slip` print format with Visitor, Security, and Approver signature spaces.
- Workflow: `Arrived -> Action Taken -> Exited`.
- Overdue reminder for visitors not exited after 6 hours or after 7:30 PM.
- Security role/user permissions for gate entry operations.

