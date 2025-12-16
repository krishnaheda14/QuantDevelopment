#!/usr/bin/env python3
"""Format and summarize last_spread_error.log for terminal output and write a debug file.

Usage:
  python tools/format_spread_error.py            # reads last_spread_error.log
  python tools/format_spread_error.py -i path   # specify log file
  python tools/format_spread_error.py -s BTCUSDT -t ETHUSDT

Output:
  - Prints a concise summary to stdout (important text only).
  - Writes a debug file at logs/last_spread_debug.log with parsed JSON and original traceback.
"""
import argparse
import json
import os
import re
from datetime import datetime


TRACE_START = "Traceback (most recent call last):"


def parse_traceback(text: str):
    lines = text.splitlines()
    # Find traceback start
    try:
        start_idx = next(i for i, l in enumerate(lines) if TRACE_START in l)
    except StopIteration:
        return None

    tb_lines = lines[start_idx:]

    # Frames: lines like:   File "path", line 123, in func
    frame_re = re.compile(r'^\s*File "(?P<file>.+?)", line (?P<line>\d+), in (?P<func>.+)$')
    frames = []
    for i, line in enumerate(tb_lines):
        m = frame_re.match(line)
        if m:
            code_line = tb_lines[i + 1].strip() if i + 1 < len(tb_lines) else ""
            frames.append({
                "file": m.group("file"),
                "line": int(m.group("line")),
                "func": m.group("func"),
                "code": code_line,
            })

    # The exception message is usually the last non-empty line
    exc_line = ""
    for l in reversed(tb_lines):
        if l.strip():
            exc_line = l.strip()
            break

    exc_type = None
    exc_msg = None
    if ": " in exc_line:
        parts = exc_line.split(": ", 1)
        exc_type = parts[0]
        exc_msg = parts[1]
    else:
        exc_msg = exc_line

    return {
        "frames": frames,
        "exception_line": exc_line,
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "raw_traceback": "\n".join(tb_lines),
    }


def summarize(parsed, symbol1=None, symbol2=None):
    lines = []
    header = f"Spread Analysis: {symbol1 or 'SYMBOL1'} vs {symbol2 or 'SYMBOL2'}"
    lines.append(header)
    lines.append("API Error: 500")
    lines.append("")
    lines.append("Internal Server Error")
    lines.append("")
    if not parsed:
        lines.append("No traceback found in file.")
        return "\n".join(lines)

    etype = parsed.get("exception_type") or "Error"
    emsg = parsed.get("exception_message") or parsed.get("exception_line")
    lines.append(f"Exception: {etype}: {emsg}")

    # Show most relevant frame (last application frame)
    frames = parsed.get("frames", [])
    if frames:
        top = frames[-1]
        lines.append(f"Location: {top['file']}:{top['line']} in {top['func']}")
        lines.append(f"Code: {top['code']}")

    # Short stack (up to 3 most relevant frames)
    lines.append("")
    lines.append("Stack (most relevant):")
    for f in frames[-3:]:
        lines.append(f" - {os.path.basename(f['file'])}:{f['line']} {f['func']} -> {f['code']}")

    return "\n".join(lines)


def write_debug_file(parsed, original_text, out_path="logs/last_spread_debug.log"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "parsed": parsed,
        "original": original_text,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", default="last_spread_error.log", help="Path to traceback log")
    p.add_argument("-s", "--symbol1", default=None)
    p.add_argument("-t", "--symbol2", default=None)
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"File not found: {args.input}")
        raise SystemExit(2)

    text = open(args.input, "r", encoding="utf-8", errors="ignore").read()
    parsed = parse_traceback(text)
    summary = summarize(parsed, args.symbol1, args.symbol2)

    # Print only the important text
    print(summary)

    # Write debug file
    out = write_debug_file(parsed or {}, text)
    print("")
    print(f"Debug file written: {out}")


if __name__ == "__main__":
    main()
