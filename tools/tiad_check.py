"""Check TwitterInternalAPIDocument's "Update Document" PR (develop -> master) before merging it and print what X changed.

    python3 ../tools/tiad_check.py                  # from the TwitterInternalAPIDocument checkout; exits 1 on an anomaly
    python3 ../tools/tiad_check.py <old> <new>      # any two commits, e.g. the parents of an earlier merge
Anomalies: a change outside docs/, a deleted file, invalid JSON, a file that lost more than 10 % of its size, a value of the
sandbox cookie in the documents, a user entity other than the sandbox account. The report lists the GraphQL operations, the
feature switches and the translation strings (en, with ja where it is translated) that were added, removed or changed.
"""
import json, os, subprocess, sys
from urllib.parse import unquote

def git(*args, **kw):
    return subprocess.run(["git", *args], capture_output=True, **kw)

git("fetch", "-q", "origin", "master", "develop", check=True)
NEW = sys.argv[2] if len(sys.argv) > 2 else "origin/develop"
OLD = sys.argv[1] if len(sys.argv) > 1 else git("merge-base", "origin/master", NEW, check=True).stdout.decode().strip()
load = lambda ref, path: json.loads(git("show", f"{ref}:{path}", check=True).stdout)
size = lambda ref, path: int(git("cat-file", "-s", f"{ref}:{path}", check=True).stdout)
cookie = {c["name"]: c["value"] for c in json.load(open(os.path.dirname(os.path.abspath(__file__)) + "/../cookie.json", encoding="utf-8"))}
me = unquote(cookie["twid"]).split("=")[1]

anomalies = []
changed = [line.split("\t") for line in git("diff", "--name-status", OLD, NEW, check=True).stdout.decode().splitlines()]
for status, path in changed:
    if not path.startswith("docs/"):
        anomalies.append(f"outside docs/: {path}")
    elif status == "D":
        anomalies.append(f"deleted: {path}")
    elif status == "M" and size(NEW, path) < 0.9 * size(OLD, path):
        anomalies.append(f"shrank: {path} {size(OLD, path)} -> {size(NEW, path)} bytes")
    if status != "D" and path.endswith(".json"):
        try:
            load(NEW, path)
        except ValueError as e:
            anomalies.append(f"invalid JSON: {path} ({e})")
secrets = "\n".join(cookie[k] for k in ("auth_token", "ct0", "kdt") if k in cookie)
if git("grep", "-q", "-F", "-f", "-", NEW, "--", "docs", input=secrets.encode()).returncode == 0:
    anomalies.append("a cookie value appears in docs/")
for path in ("docs/json/InitialState.json", "docs/deck/json/InitialState.json"):
    others = set(load(NEW, path)["entities"]["users"]["entities"]) - {me}
    if others:
        anomalies.append(f"user entities other than the sandbox account in {path}: {sorted(others)}")

def delta(title, old, new, show=lambda k, v: f"{k} = {v}"):
    rows = [f"  + {show(k, new[k])}" for k in new if k not in old] + [f"  - {show(k, old[k])}" for k in old if k not in new]
    rows += [f"  ~ {show(k, old[k])}  ->  {new[k]}" for k in new if k in old and old[k] != new[k]]
    print(f"== {title}: {len(old)} -> {len(new)}" + ("" if rows else " (no change)")); print("\n".join(rows)) if rows else None

print(f"{len(changed)} files changed, {OLD[:7]}..{NEW}")
ops = lambda ref: {e["exports"]["operationName"]: e["exports"]["queryId"] for e in load(ref, "docs/json/GraphQL.json")}
old, new = ops(OLD), ops(NEW)
delta("GraphQL operations", {k: "" for k in old}, {k: "" for k in new}, lambda k, v: k)
print("  queryId changed:", ", ".join(k for k in new if k in old and old[k] != new[k]) or "none")
switches = lambda ref: {k: v.get("value") for k, v in load(ref, "docs/json/InitialState.json")["featureSwitch"]["defaultConfig"].items()}
delta("feature switches", switches(OLD), switches(NEW))
ja = load(NEW, "docs/json/i18n/ja.json") | load(OLD, "docs/json/i18n/ja.json")
delta("translation strings (en)", load(OLD, "docs/json/i18n/en.json"), load(NEW, "docs/json/i18n/en.json"),
      lambda k, v: f"{v!r}" + (f"  [ja: {ja[k]!r}]" if ja.get(k, v) != v else ""))

print("== anomalies:", "none" if not anomalies else ""); print("\n".join(f"  ! {a}" for a in anomalies)) if anomalies else None
sys.exit(1 if anomalies else 0)
