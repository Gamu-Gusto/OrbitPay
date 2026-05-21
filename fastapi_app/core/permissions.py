from typing import List

ROLE_PERMISSIONS: dict[str, List[str]] = {
    "super_admin": [
        "MANAGE_COMPANIES",
        "DELETE_COMPANY",
        "VIEW_COMPANIES",
        "CREATE_EMPLOYEE",
        "EDIT_EMPLOYEE",
        "DELETE_EMPLOYEE",
        "VIEW_EMPLOYEES",
        "IMPORT_EMPLOYEES",
        "RUN_PAYROLL",
        "APPROVE_PAYROLL",
        "VIEW_PAYROLL",
        "VIEW_PAYROLL_REPORTS",
        "VIEW_HR_REPORTS",
        "APPROVE_LEAVE",
        "VIEW_LEAVE_REQUESTS",
        "REQUEST_DOCUMENTATION",
        "MANAGE_LEAVE_BALANCES",
        "REVIEW_DOCUMENTS",
        "APPROVE_DOCUMENTS",
        "VIEW_DOCUMENTS",
        "APPROVE_BANKING",
        "VIEW_BANKING",
        "ASSIGN_ACCOUNTANTS",
        "MANAGE_ASSIGNMENTS",
        "VIEW_AUDIT_LOGS",
        "VIEW_ALL_REPORTS",
        "CREATE_USER",
        "DEACTIVATE_USER",
    ],
    "accountant": [
        "MANAGE_COMPANIES",
        "VIEW_COMPANIES",
        "CREATE_EMPLOYEE",
        "EDIT_EMPLOYEE",
        "DELETE_EMPLOYEE",
        "VIEW_EMPLOYEES",
        "IMPORT_EMPLOYEES",
        "RUN_PAYROLL",
        "VIEW_PAYROLL",
        "VIEW_PAYROLL_REPORTS",
        "VIEW_LEAVE_REQUESTS",
        "MANAGE_LEAVE_BALANCES",
        "VIEW_DOCUMENTS",
        "VIEW_BANKING",
        "VIEW_HR_REPORTS",
        "VIEW_AUDIT_LOGS",
    ],
    "employee": [
        "VIEW_OWN_PAYSLIPS",
        "VIEW_OWN_LEAVE",
        "APPLY_LEAVE",
        "UPLOAD_DOCUMENTS",
        "SUBMIT_BANKING_CHANGE",
        "UPDATE_PASSWORD",
        "VIEW_OWN_PAYROLL_HISTORY",
    ],
}


def get_permissions_for_roles(role_names: List[str]) -> List[str]:
    perms: set[str] = set()
    for role in role_names:
        perms.update(ROLE_PERMISSIONS.get(role, []))
    return list(perms)


def has_permission(role_names: List[str], permission: str) -> bool:
    return permission in get_permissions_for_roles(role_names)
