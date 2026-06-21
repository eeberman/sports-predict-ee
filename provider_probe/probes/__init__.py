from dataclasses import dataclass, field


@dataclass
class ProbeResult:
    provider: str
    data_area: str
    status: str                      # "ok", "partial", "error", "skipped"
    api_key_present: bool
    fields_found: list[str] = field(default_factory=list)
    fields_missing: list[str] = field(default_factory=list)
    notes: str = ""
    raw_sample_path: str | None = None
