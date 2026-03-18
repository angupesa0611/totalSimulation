#!/usr/bin/env python3
"""Submit all tool presets via POST /api/simulate and track results.

Usage: python3 scripts/test_all_presets.py [--timeout 120] [--filter rayoptics]
"""

import argparse
import json
import sys
import time

import requests

BASE = "http://localhost:8000"


def submit_and_poll(preset_key, params, timeout=120):
    """Submit a simulation and poll until completion or timeout."""
    try:
        resp = requests.post(
            f"{BASE}/api/simulate",
            json={"tool": params["tool"], "params": params.get("params", {}), "project": "_test"},
            timeout=10,
        )
        if resp.status_code != 200:
            return "SUBMIT_ERROR", resp.text[:200]
        job_id = resp.json().get("job_id")
        if not job_id:
            return "NO_JOB_ID", resp.text[:200]
    except Exception as e:
        return "CONNECTION_ERROR", str(e)[:200]

    # Poll for result
    start = time.time()
    while time.time() - start < timeout:
        try:
            status_resp = requests.get(f"{BASE}/api/status/{job_id}", timeout=10)
            if status_resp.status_code != 200:
                time.sleep(2)
                continue
            data = status_resp.json()
            state = data.get("status", data.get("state", "UNKNOWN"))
            if state == "SUCCESS":
                return "SUCCESS", job_id
            elif state == "FAILURE":
                error = data.get("message", data.get("error", data.get("result", "unknown error")))
                return "FAILURE", str(error)[:300]
            elif state in ("PENDING", "PROGRESS", "STARTED"):
                time.sleep(2)
                continue
            else:
                time.sleep(2)
        except Exception as e:
            time.sleep(2)

    return "TIMEOUT", f"job_id={job_id}, waited {timeout}s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=120, help="Per-preset timeout in seconds")
    parser.add_argument("--filter", type=str, default=None, help="Only test presets matching this substring")
    args = parser.parse_args()

    # Get all presets
    resp = requests.get(f"{BASE}/api/presets")
    presets = resp.json()

    if args.filter:
        presets = [p for p in presets if args.filter in p["key"]]

    print(f"Testing {len(presets)} tool presets (timeout={args.timeout}s each)\n")
    print(f"{'#':<4} {'Preset':<40} {'Status':<12} {'Detail'}")
    print("-" * 100)

    results = {"SUCCESS": 0, "FAILURE": 0, "TIMEOUT": 0, "SUBMIT_ERROR": 0, "CONNECTION_ERROR": 0, "NO_JOB_ID": 0}

    for i, preset in enumerate(presets, 1):
        key = preset["key"]

        # Fetch full params
        try:
            params_resp = requests.get(f"{BASE}/api/presets/{key}", timeout=10)
            params = params_resp.json()
        except Exception as e:
            print(f"{i:<4} {key:<40} {'FETCH_ERR':<12} {e}")
            continue

        status, detail = submit_and_poll(key, params, timeout=args.timeout)
        results[status] = results.get(status, 0) + 1

        marker = "✓" if status == "SUCCESS" else "✗"
        detail_short = detail[:55] if len(str(detail)) > 55 else detail
        print(f"{i:<4} {key:<40} {marker} {status:<12} {detail_short}")

    print("\n" + "=" * 100)
    print(f"Results: {results}")
    total = sum(results.values())
    print(f"Pass rate: {results['SUCCESS']}/{total} ({100*results['SUCCESS']/total:.0f}%)")

    sys.exit(0 if results["FAILURE"] == 0 and results["TIMEOUT"] == 0 else 1)


if __name__ == "__main__":
    main()
