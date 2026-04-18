from __future__ import annotations

import time
from typing import Any, Callable, Dict, List

from .adapters.base import BaseAdapter
from .utils import now_utc

TERMINAL_STATUSES = {
    "FINALIZED",
    "OUT_OF_FEE",
    "FAILED",
    "REJECTED",
    "ERROR",
    "DROPPED",
    "CANCELED",
    "UNDETERMINED",
    "VALIDATORS_TIMEOUT",
    "LEADER_TIMEOUT",
}

# Statuses that indicate transaction is being processed
PROCESSING_STATUSES = {
    "PENDING",
    "COMMITTING",
    "REVEALING",
    "PROPOSING",
}


def wait_for_status(
    adapter: BaseAdapter,
    tx_hash: str,
    wait_status: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
    network: str | None = None,
    on_status: Callable[[str, Dict[str, Any]], None] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    started = time.monotonic()
    timeline: List[Dict[str, Any]] = []
    target = (wait_status or "accepted").lower()
    seen_status = None
    tx_found = False
    poll_count = 0
    last_log_time = started

    while True:
        poll_count += 1
        elapsed = time.monotonic() - started

        try:
            status_payload = adapter.get_status(tx_hash, network=network)
            status = str(status_payload.get("status", "UNKNOWN")).upper()

            # Check if transaction exists in blockchain
            if not tx_found and status != "UNKNOWN":
                tx_found = True
                timeline.append(
                    {
                        "event": "transaction_found",
                        "status": status,
                        "checked_at": now_utc().isoformat(),
                        "elapsed_seconds": round(elapsed, 2),
                        "poll_count": poll_count,
                    }
                )
                if on_status is not None:
                    on_status(f"FOUND_{status}", status_payload)

            # Log status changes
            if status != seen_status:
                timeline.append(
                    {
                        "status": status,
                        "checked_at": now_utc().isoformat(),
                        "elapsed_seconds": round(elapsed, 2),
                        "poll_count": poll_count,
                        "payload": status_payload,
                    }
                )
                if on_status is not None:
                    on_status(status, status_payload)
                seen_status = status

            # Log progress every 30 seconds if still processing
            if tx_found and status in PROCESSING_STATUSES:
                if elapsed - last_log_time >= 30:
                    if on_status is not None:
                        on_status(
                            f"{status}_PROGRESS",
                            {
                                "status": status,
                                "elapsed_seconds": round(elapsed, 2),
                                "poll_count": poll_count,
                                "message": f"Still processing after {round(elapsed)}s ({poll_count} polls)",
                            },
                        )
                    last_log_time = elapsed

            # Check if target status is reached
            if tx_found:
                if target == "accepted" and status in {
                    "ACCEPTED",
                    "FINALIZED",
                    *TERMINAL_STATUSES,
                }:
                    timeline.append(
                        {
                            "event": "target_reached",
                            "status": status,
                            "checked_at": now_utc().isoformat(),
                            "elapsed_seconds": round(elapsed, 2),
                            "poll_count": poll_count,
                        }
                    )
                    return timeline, status_payload
                if target == "finalized" and status in TERMINAL_STATUSES:
                    timeline.append(
                        {
                            "event": "target_reached",
                            "status": status,
                            "checked_at": now_utc().isoformat(),
                            "elapsed_seconds": round(elapsed, 2),
                            "poll_count": poll_count,
                        }
                    )
                    return timeline, status_payload

        except Exception as e:
            # If we get an error, transaction might not exist yet
            # Continue polling until timeout
            if not tx_found:
                # Log every 30 seconds while waiting for transaction to appear
                if elapsed - last_log_time >= 30:
                    if on_status is not None:
                        on_status(
                            "WAITING_FOR_TX",
                            {
                                "message": f"Waiting for transaction to appear in blockchain ({round(elapsed)}s, {poll_count} polls)",
                                "error": str(e),
                            },
                        )
                    last_log_time = elapsed
            else:
                # If transaction was found before but now we get error, log and continue
                timeline.append(
                    {
                        "event": "polling_error",
                        "error": str(e),
                        "checked_at": now_utc().isoformat(),
                        "elapsed_seconds": round(elapsed, 2),
                    }
                )

        # Check timeout
        if elapsed > timeout_seconds:
            if not tx_found:
                raise TimeoutError(
                    f"Timed out waiting for tx {tx_hash} to appear in blockchain after {round(elapsed)}s ({poll_count} polls)"
                )
            else:
                raise TimeoutError(
                    f"Timed out waiting for tx {tx_hash} to reach {wait_status} after {round(elapsed)}s ({poll_count} polls). Last status: {seen_status}"
                )

        time.sleep(poll_interval_seconds)
