import os


def is_demo_workspace(workspace_id: int) -> bool:
    configured_id = os.getenv("CUSTOMER_SUPPORT_DEMO_WORKSPACE_ID", "").strip()
    if not configured_id:
        return False
    try:
        return int(configured_id) == int(workspace_id)
    except (TypeError, ValueError):
        return False
