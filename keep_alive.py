#!/usr/bin/env python3
"""
keep_alive.py
=============
Keep Render and Supabase free-tier instances active and prevent idle spin-down.

Features:
- Pings your Render web service (specifically /healthz) every 10-14 minutes
  (Render free tier sleeps after 15 mins of inactivity).
- The /healthz endpoint executes a 'SELECT 1' against Supabase Postgres,
  keeping both Render and Supabase active in a single ping.
- Optionally pings Supabase REST API directly as an extra safety measure.
- Runs without third-party dependencies (uses standard library `urllib`).
- Supports both continuous loop mode (daemon) and single ping mode (--once for crons).
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from urllib import error, request


def load_env_file(filepath=".env"):
    """Lightweight .env loader if python-dotenv is not installed."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", flush=True)


def ping_url(url, headers=None, timeout=60):
    """Send an HTTP GET request and return (status_code, response_text, latency_seconds)."""
    headers = headers or {"User-Agent": "Render-Supabase-KeepAlive/1.0"}
    req = request.Request(url, headers=headers, method="GET")
    start = time.time()
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            latency = round(time.time() - start, 2)
            body = resp.read().decode("utf-8", errors="replace").strip()
            return resp.status, body, latency
    except error.HTTPError as e:
        latency = round(time.time() - start, 2)
        body = e.read().decode("utf-8", errors="replace").strip()
        return e.code, body, latency
    except Exception as e:
        latency = round(time.time() - start, 2)
        return None, str(e), latency


def ping_render(app_url):
    """Pings the Render app's /healthz endpoint."""
    if not app_url.startswith("http://") and not app_url.startswith("https://"):
        app_url = "https://" + app_url
    endpoint = app_url.rstrip("/")
    if not endpoint.endswith("/healthz"):
        endpoint += "/healthz"

    log(f"Pinging Render endpoint: {endpoint}")
    status, body, latency = ping_url(endpoint)

    if status == 200:
        log(f"Render ping SUCCESS: HTTP 200 ({latency}s) - {body}", "SUCCESS")
        return True
    elif status is not None:
        log(f"Render ping WARNING: HTTP {status} ({latency}s) - {body}", "WARNING")
        return True  # Server responded, so Render woke up
    else:
        log(f"Render ping FAILED: ({latency}s) - Error: {body}", "ERROR")
        return False


def ping_supabase(supabase_url, supabase_key):
    """Directly pings Supabase REST API as an auxiliary health check."""
    if not supabase_url:
        return
    endpoint = supabase_url.rstrip("/") + "/rest/v1/"
    headers = {
        "apikey": supabase_key or "",
        "Authorization": f"Bearer {supabase_key}" if supabase_key else "",
        "User-Agent": "Render-Supabase-KeepAlive/1.0",
    }
    log(f"Pinging Supabase REST: {endpoint}")
    status, body, latency = ping_url(endpoint, headers=headers)
    if status in (200, 401, 404):  # Any response shows the database/API gateway is alive
        log(f"Supabase ping OK: HTTP {status} ({latency}s)", "SUCCESS")
    else:
        log(f"Supabase ping note: HTTP {status} ({latency}s) - {body}", "WARNING")


def main():
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Keep Render web service and Supabase database alive."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("RENDER_URL") or os.environ.get("APP_URL"),
        help="Base URL of your Render app (e.g. https://bartersys.onrender.com)",
    )
    parser.add_argument(
        "--supabase-url",
        default=os.environ.get("SUPABASE_URL"),
        help="Optional Supabase project URL",
    )
    parser.add_argument(
        "--supabase-key",
        default=os.environ.get("SUPABASE_KEY"),
        help="Optional Supabase anon key",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("KEEP_ALIVE_INTERVAL", 780)),
        help="Ping interval in seconds (default: 780s = 13 minutes)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Perform a single ping and exit (ideal for cron jobs / GitHub Actions)",
    )

    args = parser.parse_args()

    if not args.url:
        log("No Render URL provided.", "ERROR")
        print("\nUsage:")
        print("  python keep_alive.py --url https://your-app.onrender.com")
        print("Or set RENDER_URL in your .env file:")
        print("  RENDER_URL=https://your-app.onrender.com\n")
        sys.exit(1)

    log(f"Starting keep-alive service for Render & Supabase.")
    log(f"Target Render URL: {args.url}")
    log(f"Interval: {args.interval} seconds (~{args.interval // 60} mins)")

    while True:
        ping_render(args.url)
        if args.supabase_url:
            ping_supabase(args.supabase_url, args.supabase_key)

        if args.once:
            break

        log(f"Sleeping for {args.interval}s until next ping...")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            log("Keep-alive service stopped by user.", "INFO")
            break


if __name__ == "__main__":
    main()
