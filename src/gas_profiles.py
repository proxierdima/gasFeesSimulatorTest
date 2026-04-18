from __future__ import annotations

from .models import AppSettings, GasProfile


def resolve_gaslimit(profile: GasProfile, settings: AppSettings) -> tuple[int, str]:
    if profile.mode == "custom" and profile.gaslimit is not None:
        return int(profile.gaslimit), f"custom:{profile.gaslimit}"

    preset = (profile.preset or "normal").lower()
    thresholds = settings.gas_thresholds

    mapping = {
        "low": max(1, thresholds.fail_below - 5),
        "borderline": thresholds.borderline_below,
        "normal": thresholds.normal,
        "high": thresholds.high,
    }
    gaslimit = mapping.get(preset, thresholds.normal)
    return gaslimit, f"preset:{preset}"
