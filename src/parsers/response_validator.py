from dataclasses import dataclass

class ValidationError(ValueError):
    pass

@dataclass
class Limits:
    min_start: int = 0
    min_limit: int = 1
    max_limit: int = 1000
    min_pages: int = 1
    max_pages: int = 20

def validate_input(*, start: int, limit: int, pages: int, limits: Limits = Limits()) -> None:
    if start < limits.min_start:
        raise ValidationError(f"start must be >= {limits.min_start}")
    if not (limits.min_limit <= limit <= limits.max_limit):
        raise ValidationError(f"limit must be between {limits.min_limit} and {limits.max_limit}")
    if not (limits.min_pages <= pages <= limits.max_pages):
        raise ValidationError(f"pages must be between {limits.min_pages} and {limits.max_pages}")