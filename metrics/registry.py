from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Optional, Tuple

LabelKey = Tuple[Tuple[str, str], ...]


def _normalize_labels(labels: Optional[Dict[str, str]]) -> LabelKey:
    if not labels:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
    return f'"{escaped}"'


def _format_labels(labels: Dict[str, str]) -> str:
    if not labels:
        return ""
    return "{" + ",".join(f"{k}={_quote(v)}" for k, v in sorted(labels.items())) + "}"


class Counter:
    def __init__(self, name: str, help_text: str) -> None:
        self.name = name
        self.help = help_text
        self._values: Dict[LabelKey, float] = defaultdict(float)

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        key = _normalize_labels(labels)
        self._values[key] += amount

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} counter"
        for labels, value in self._values.items():
            yield f"{self.name}{_format_labels(dict(labels))} {value}"


class Gauge:
    def __init__(self, name: str, help_text: str) -> None:
        self.name = name
        self.help = help_text
        self._values: Dict[LabelKey, float] = defaultdict(float)

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        key = _normalize_labels(labels)
        self._values[key] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        key = _normalize_labels(labels)
        self._values[key] += amount

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} gauge"
        for labels, value in self._values.items():
            yield f"{self.name}{_format_labels(dict(labels))} {value}"


class Histogram:
    def __init__(self, name: str, help_text: str, buckets: Optional[Iterable[float]] = None) -> None:
        self.name = name
        self.help = help_text
        self.buckets = sorted(buckets or [0.1, 0.3, 1, 3, 10])
        self._bucket_counts: Dict[LabelKey, Dict[float, float]] = defaultdict(lambda: defaultdict(float))
        self._sum: Dict[LabelKey, float] = defaultdict(float)
        self._count: Dict[LabelKey, float] = defaultdict(float)

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        key = _normalize_labels(labels)
        self._count[key] += 1
        self._sum[key] += value
        for bucket in self.buckets:
            if value <= bucket:
                self._bucket_counts[key][bucket] += 1
        self._bucket_counts[key][float("inf")] += 1

    def render(self) -> Iterable[str]:
        yield f"# HELP {self.name} {self.help}"
        yield f"# TYPE {self.name} histogram"
        for labels, buckets in self._bucket_counts.items():
            base_labels = dict(labels)
            cumulative = 0.0
            for bucket in self.buckets + [float("inf")]:
                cumulative = buckets.get(bucket, cumulative)
                label_dict = dict(base_labels)
                label_dict["le"] = "+inf" if bucket == float("inf") else str(bucket)
                yield f"{self.name}_bucket{_format_labels(label_dict)} {cumulative}"
            yield f"{self.name}_sum{_format_labels(base_labels)} {self._sum[labels]}"
            yield f"{self.name}_count{_format_labels(base_labels)} {self._count[labels]}"


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}

    def counter(self, name: str, help_text: str) -> Counter:
        return self._counters.setdefault(name, Counter(name, help_text))

    def gauge(self, name: str, help_text: str) -> Gauge:
        return self._gauges.setdefault(name, Gauge(name, help_text))

    def histogram(self, name: str, help_text: str, buckets: Optional[Iterable[float]] = None) -> Histogram:
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, help_text, buckets)
        return self._histograms[name]

    def render_prometheus(self) -> str:
        lines: list[str] = []
        for metric in self._counters.values():
            lines.extend(metric.render())
        for metric in self._gauges.values():
            lines.extend(metric.render())
        for metric in self._histograms.values():
            lines.extend(metric.render())
        return "\n".join(lines) + "\n"
