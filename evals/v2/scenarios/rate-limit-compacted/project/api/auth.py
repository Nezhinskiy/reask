from api.store import keys


def api_key_from(request):
    key = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if key not in keys.active():
        raise PermissionError(401)
    return key
