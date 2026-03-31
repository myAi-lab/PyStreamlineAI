from app.core.correlation import get_request_id


def ok(data: object) -> dict:
    return {"success": True, "data": data, "request_id": get_request_id()}

