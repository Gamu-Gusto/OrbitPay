from fastapi import HTTPException

# Valid status values
LEAVE_STATUSES = {"pending", "under_review", "request_documentation", "approved", "rejected"}

# Allowed transitions: current_status -> set of reachable statuses
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending":               {"under_review", "approved", "rejected", "request_documentation"},
    "under_review":          {"approved", "rejected", "request_documentation"},
    "request_documentation": {"pending"},   # employee re-submits docs → back to pending
    "approved":              set(),
    "rejected":              set(),
}


def assert_transition(current: str, target: str) -> None:
    """Raise 409 if the target status is not reachable from the current one."""
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition leave request from '{current}' to '{target}'",
        )
