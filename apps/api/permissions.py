from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnly(BasePermission):
    """Anonymous, read-only access: GET/HEAD/OPTIONS only, for everyone.

    Deny-by-default for any write method, regardless of who is asking --
    nothing in this API is writable, so nothing should ever be allowed to try.
    """

    def has_permission(self, request, view) -> bool:
        return request.method in SAFE_METHODS
