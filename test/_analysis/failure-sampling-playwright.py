"""Sample and see results"""
#!/usr/bin/env python3
import argparse, os, re, sys
from datetime import datetime
from collections import defaultdict, OrderedDict

FAILURE_HEADER_RE = re.compile(
    r'^\s*\d+\)\s*(?:\[[^\]]+\]\s*›\s*)?'
    r'(?P<file>.+?):\d+:\d+\s*›\s*(?P<name>.+)$'
)
RUN_MARKER_RE = re.compile(r'^make: \*\*\* \[frontend-test-e2e\] Error 1\s*$')

def read_all_text(paths: list[str]) -> str:
    if not paths:
        return sys.stdin.read()
    buf = []
    for p in paths:
        with open(p, 'r', errors='replace') as f:
            buf.append(f.read())
    return "\n".join(buf)

def parse(log_text: str):
    lines = log_text.splitlines()
    total_runs = sum(1 for ln in lines if RUN_MARKER_RE.match(ln))
    failures: dict[tuple[str,str], dict] = {}
    counts = defaultdict(int)

    i, n = 0, len(lines)
    while i < n:
        m = FAILURE_HEADER_RE.match(lines[i])
        if m:
            raw_file = m.group('file').strip()
            file_only = raw_file.split(' ')[0]  # trim any trailing tokens
            file_only = file_only.split(':')[0] # drop :line:col if present
            name = m.group('name').strip()

            key = (file_only, name)
            counts[key] += 1
            if key not in failures:
                # capture a sample block until next failure header or EOF
                j = i + 1
                block = []
                while j < n and not FAILURE_HEADER_RE.match(lines[j]):
                    block.append(lines[j])
                    j += 1
                failures[key] = {
                    "file": file_only,
                    "name": name,
                    "sample": "\n".join(block).rstrip()
                }
                i = j
                continue
        i += 1

    # Combine counts into ordered list (desc by count, then name)
    items = sorted(
        ((f["file"], f["name"], counts[(f["file"], f["name"])], f["sample"])
         for f in failures.values()),
        key=lambda x: (-x[2], x[0], x[1])
    )
    return items, max(total_runs, 1)  # avoid div-by-zero

def write_report(items, total_runs, out_dir="output/failure-sampling"):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(out_dir, f"{ts}.txt")

    # Markdown table header
    lines = []
    lines.append("| # | file | name | n | % |")
    lines.append("| -: | --- | --- | -: | -: |")

    for idx, (file_path, name, n, _) in enumerate(items, start=1):
        pct = (n / total_runs) * 100.0
        lines.append(f"| {idx} | `{file_path}` | {name} | {n} | {pct:.1f} |")

    lines.append("")  # spacer

    # Detailed samples
    for idx, (file_path, name, n, sample) in enumerate(items, start=1):
        header = f"{idx}) {file_path} › {name}"
        lines.append("```")
        lines.append(f"  {header}\n")
        # ensure there is at least something in sample
        sample_text = sample if sample.strip() else "(no sample block captured)"
        lines.append(sample_text)
        lines.append("```")
        lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    return out_path

def main():
    ap = argparse.ArgumentParser(
        description="Analyze Playwright e2e log(s) for failing tests."
    )
    ap.add_argument(
        "logs", nargs="*", help="Log file(s). If none, read from stdin.", default=["input/logs.txt"]
    )
    ap.add_argument(
        "--outdir", default="output/failure-sampling",
        help="Output directory (default: output/failure-sampling)"
    )
    args = ap.parse_args()

    text = read_all_text(args.logs)
    items, total_runs = parse(text)
    out_path = write_report(items, total_runs, args.outdir)
    print(f"Wrote: {out_path}")
    print(f"Total runs counted (by marker): {total_runs}")
    if not items:
        print("No failures detected via Playwright-style headers.")

if __name__ == "__main__":
    main()
