#!/usr/bin/env python3
"""Submit pipeline and coupling presets via POST /api/pipeline and track results.

Usage: python3 scripts/test_pipeline_presets.py [--timeout 180] [--type pipelines|couplings] [--filter keyword]
"""

import argparse
import json
import sys
import time

import requests

BASE = "http://localhost:8000"


def submit_and_poll(preset_key, payload, timeout=180):
    """Submit a pipeline and poll until completion or timeout."""
    try:
        resp = requests.post(
            f"{BASE}/api/pipeline",
            json={
                "steps": payload["steps"],
                "project": "_test",
                "label": payload.get("label", preset_key),
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return "SUBMIT_ERROR", resp.text[:300]
        data = resp.json()
        pipeline_id = data.get("pipeline_id")
        if not pipeline_id:
            return "NO_PIPELINE_ID", resp.text[:200]
    except Exception as e:
        return "CONNECTION_ERROR", str(e)[:200]

    # Poll for result
    start = time.time()
    while time.time() - start < timeout:
        try:
            status_resp = requests.get(f"{BASE}/api/pipeline/{pipeline_id}", timeout=10)
            if status_resp.status_code != 200:
                time.sleep(3)
                continue
            data = status_resp.json()
            state = data.get("status", data.get("state", "UNKNOWN"))
            if state in ("completed", "SUCCESS"):
                return "SUCCESS", pipeline_id
            elif state in ("failed", "FAILURE", "FAILED"):
                # Find which step failed
                steps = data.get("steps", [])
                for s in steps:
                    if s.get("status") in ("failed", "FAILURE", "FAILED"):
                        err = s.get("error", s.get("message", "unknown"))
                        return "FAILURE", f"step {s.get('tool','?')}: {str(err)[:200]}"
                return "FAILURE", str(data.get("error", "unknown"))[:300]
            elif state in ("running", "pending", "PENDING", "PROGRESS", "STARTED", "RUNNING"):
                time.sleep(3)
                continue
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)

    # On timeout, report which step is stuck
    try:
        status_resp = requests.get(f"{BASE}/api/pipeline/{pipeline_id}", timeout=10)
        data = status_resp.json()
        steps = data.get("steps", [])
        stuck = [s for s in steps if s.get("status") not in ("completed", "failed", "SUCCESS", "FAILURE")]
        if stuck:
            return "TIMEOUT", f"stuck at step: {stuck[0].get('tool','?')} (pid={pipeline_id})"
    except Exception:
        pass
    return "TIMEOUT", f"pipeline_id={pipeline_id}, waited {timeout}s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=180, help="Per-preset timeout in seconds")
    parser.add_argument("--type", choices=["pipelines", "couplings", "all"], default="all")
    parser.add_argument("--filter", type=str, default=None, help="Only test presets matching this substring")
    args = parser.parse_args()

    presets = []

    if args.type in ("pipelines", "all"):
        resp = requests.get(f"{BASE}/api/presets/pipelines")
        for p in resp.json():
            presets.append(("pipeline", p["key"]))

    if args.type in ("couplings", "all"):
        resp = requests.get(f"{BASE}/api/presets/couplings")
        for p in resp.json():
            presets.append(("coupling", p["key"]))

    if args.filter:
        presets = [(t, k) for t, k in presets if args.filter in k]

    print(f"Testing {len(presets)} presets (timeout={args.timeout}s each)\n")
    print(f"{'#':<4} {'Type':<10} {'Preset':<45} {'Status':<12} {'Detail'}")
    print("-" * 120)

    results = {"SUCCESS": 0, "FAILURE": 0, "TIMEOUT": 0, "SUBMIT_ERROR": 0,
               "CONNECTION_ERROR": 0, "NO_PIPELINE_ID": 0}

    for i, (ptype, key) in enumerate(presets, 1):
        # Fetch full preset payload
        try:
            endpoint = "pipelines" if ptype == "pipeline" else "couplings"
            params_resp = requests.get(f"{BASE}/api/presets/{endpoint}/{key}", timeout=10)
            if params_resp.status_code != 200:
                print(f"{i:<4} {ptype:<10} {key:<45} {'FETCH_ERR':<12} HTTP {params_resp.status_code}")
                continue
            payload = params_resp.json()
        except Exception as e:
            print(f"{i:<4} {ptype:<10} {key:<45} {'FETCH_ERR':<12} {e}")
            continue

        status, detail = submit_and_poll(key, payload, timeout=args.timeout)
        results[status] = results.get(status, 0) + 1

        marker = "\u2713" if status == "SUCCESS" else "\u2717"
        detail_short = str(detail)[:55] if len(str(detail)) > 55 else detail
        print(f"{i:<4} {ptype:<10} {key:<45} {marker} {status:<12} {detail_short}")

    print("\n" + "=" * 120)
    print(f"Results: {results}")
    total = sum(results.values())
    if total > 0:
        print(f"Pass rate: {results['SUCCESS']}/{total} ({100*results['SUCCESS']/total:.0f}%)")

    sys.exit(0 if results["FAILURE"] == 0 and results["TIMEOUT"] == 0 else 1)


if __name__ == "__main__":
    main()
