class FriendlyError(RuntimeError):
    pass


class QuotaExceededError(FriendlyError):
    pass


class SheetNotFoundError(FriendlyError):
    pass


class PermissionDeniedError(FriendlyError):
    pass
