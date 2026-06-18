from dataclasses import dataclass

from ..enums import enum_values


ATTEMPT_STATUSES = tuple(enum_values("attempt_status"))
METRIC_STATUS_ORDER = (
    "missing",
    "in_progress",
    "expired",
    "voided",
    "submitted",
    "needs_grading",
    "graded",
)
METRIC_STATUSES = tuple(
    status for status in METRIC_STATUS_ORDER if status == "missing" or status in ATTEMPT_STATUSES
)
DEFAULT_STATUSES = tuple(status for status in METRIC_STATUSES if status != "voided")
MODES = ("latest", "all")


class MetricsFilterError(ValueError):
    pass


@dataclass(frozen=True)
class MetricsFilters:
    mode: str = "latest"
    statuses: tuple[str, ...] = DEFAULT_STATUSES
    include_voided: bool = False
    quiz_version_id: int | None = None
    quiz_version_ids: tuple[int, ...] = ()

    def __post_init__(self):
        quiz_ids = tuple(int(value) for value in self.quiz_version_ids)
        if self.quiz_version_id is not None:
            quiz_ids = (int(self.quiz_version_id), *quiz_ids)
        quiz_ids = tuple(dict.fromkeys(quiz_ids))
        object.__setattr__(self, "quiz_version_ids", quiz_ids)
        object.__setattr__(
            self,
            "quiz_version_id",
            quiz_ids[0] if len(quiz_ids) == 1 else None,
        )

    @property
    def attempt_statuses(self):
        return tuple(status for status in self.statuses if status != "missing")

    @property
    def includes_missing(self):
        return "missing" in self.statuses

    def to_payload(self):
        return {
            "mode": self.mode,
            "statuses": list(self.statuses),
            "include_voided": self.include_voided,
            "quiz_version_id": self.quiz_version_id,
            "quiz_version_ids": list(self.quiz_version_ids),
            "included_statuses": {
                "missing": self.includes_missing,
                "in_progress": "in_progress" in self.statuses,
                "submitted": "submitted" in self.statuses,
                "needs_grading": "needs_grading" in self.statuses,
                "graded": "graded" in self.statuses,
                "expired": "expired" in self.statuses,
                "voided": self.include_voided and "voided" in self.statuses,
            },
            "rollup_attempts": (
                "latest non-voided attempt per student per quiz version"
                if self.mode == "latest" and not self.include_voided
                else "latest attempt per student per quiz version"
                if self.mode == "latest"
                else "all matching attempts"
            ),
            "voided_policy": (
                "included only because include_voided is true"
                if self.include_voided
                else "excluded by default"
            ),
            "expired_unanswered_policy": (
                "expired attempts count unanswered finalized questions as zero "
                "unless expired attempts are filtered out"
            ),
        }


def parse_metrics_filters(args):
    include_voided = _bool_arg(args, "include_voided", default=False)
    mode = _string_arg(args, "mode", "latest").lower()
    if mode not in MODES:
        raise MetricsFilterError("mode must be latest or all")

    explicit_statuses = _status_values(args)
    if explicit_statuses:
        statuses = _ordered_statuses(explicit_statuses)
        if "voided" in statuses:
            include_voided = True
    else:
        statuses = tuple(METRIC_STATUSES if include_voided else DEFAULT_STATUSES)

    if not include_voided:
        statuses = tuple(status for status in statuses if status != "voided")

    if not statuses:
        raise MetricsFilterError("at least one status must be included")

    quiz_version_ids = _positive_int_values(args, "quiz_version_id")
    quiz_version_ids += _positive_int_values(args, "quiz_version_ids")
    return MetricsFilters(
        mode=mode,
        statuses=statuses,
        include_voided=include_voided,
        quiz_version_ids=tuple(dict.fromkeys(quiz_version_ids)),
    )


def _status_values(args):
    raw_values = []
    for key in ("status", "statuses"):
        raw_values.extend(_list_arg(args, key))

    statuses = []
    for raw_value in raw_values:
        for part in str(raw_value).split(","):
            normalized = part.strip().lower().replace("-", "_")
            if not normalized:
                continue
            if normalized not in METRIC_STATUSES:
                raise MetricsFilterError(f"unknown status filter: {part.strip()}")
            statuses.append(normalized)
    return statuses


def _ordered_statuses(statuses):
    included = set(statuses)
    return tuple(status for status in METRIC_STATUS_ORDER if status in included)


def _string_arg(args, key, default):
    getter = getattr(args, "get", None)
    if getter is None:
        return str(args.get(key, default) if isinstance(args, dict) else default)
    value = getter(key, default)
    return str(default if value is None else value).strip()


def _list_arg(args, key):
    getter = getattr(args, "getlist", None)
    if getter is not None:
        return getter(key)
    value = args.get(key) if isinstance(args, dict) else None
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _bool_arg(args, key, *, default=False):
    value = _string_arg(args, key, "")
    if value == "":
        return default
    value = value.lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise MetricsFilterError(f"{key} must be a boolean")


def _optional_positive_int_arg(args, key):
    value = _string_arg(args, key, "")
    if value == "":
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise MetricsFilterError(f"{key} must be an integer") from exc
    if parsed <= 0:
        raise MetricsFilterError(f"{key} must be positive")
    return parsed


def _positive_int_values(args, key):
    parsed_values = []
    for raw_value in _list_arg(args, key):
        for part in str(raw_value).split(","):
            value = part.strip()
            if not value:
                continue
            try:
                parsed = int(value)
            except ValueError as exc:
                raise MetricsFilterError(f"{key} must be an integer") from exc
            if parsed <= 0:
                raise MetricsFilterError(f"{key} must be positive")
            parsed_values.append(parsed)
    return parsed_values
