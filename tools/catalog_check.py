"""Cross-check a recording of twitter-api-safe-dump made with wire_tee.mjs before it goes into the placeholder.

    cd twitter-openapi && uv run python ../tools/catalog_check.py <recording dir>
<recording dir> holds the dump's requests.ndjson and the tee's wire.ndjson. Reports: catalog lines without an identical
request on the wire (queryId, variables, features, fieldToggles), operations that used more than one queryId or
feature set in the session, and per placeholder entry what the session changes, with the queryId of
../TwitterInternalAPIDocument (origin/develop as last fetched) next to it. Prints names, ids and key names only.
"""
import collections, json, re, subprocess, sys
from urllib.parse import parse_qs, urlparse

rec, placeholder_path, tiad_dir, catalog_name = sys.argv[1], "src/config/placeholder.json", "../TwitterInternalAPIDocument", "requests.ndjson"
GQL = re.compile(r"/graphql/(?P<id>[^/]+)/(?P<name>[^/?]+)")
KEYS = ["variables", "features", "fieldToggles"]

def wire_payload(method, url, post):
    if method == "GET":
        q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        return {k: json.loads(q[k]) for k in KEYS if k in q}
    data = json.loads(post or "{}")
    return {k: data[k] for k in KEYS if k in data}

wire = collections.defaultdict(list)  # (name, method) -> [(at, id, payload, page)]
statuses = collections.Counter(); not200 = collections.Counter()
for line in open(f"{rec}/wire.ndjson"):
    e = json.loads(line)
    m = GQL.search(urlparse(e["url"]).path)
    if "status" in e:
        statuses[e["status"]] += 1
        if e["status"] != 200:
            not200[(m["name"] if m else urlparse(e["url"]).path, e["status"])] += 1
        continue
    if m:
        wire[(m["name"], e["method"])].append((e["at"], m["id"], wire_payload(e["method"], e["url"], e.get("postData")), e.get("page")))

hook = {}
for line in open(f"{rec}/{catalog_name}"):
    r = json.loads(line)
    m = GQL.fullmatch(r["path"])
    if m is None:
        continue
    src = r.get("params", {}) if r["method"] == "GET" else r.get("data", {})
    payload = {k: (json.loads(src[k]) if isinstance(src[k], str) else src[k]) for k in KEYS if k in src}
    hook[(m["name"], r["method"])] = (m["id"], payload, r.get("recordedAt"))

print(f"wire: {sum(len(v) for v in wire.values())} GraphQL requests, {len(wire)} (operation, method) pairs, {len({n for n, _ in wire})} operations")
print("wire response statuses:", dict(statuses), "| not 200:", {f"{k[0]} {k[1]}": v for k, v in not200.items()})
print(f"hook catalog: {len(hook)} GraphQL (operation, method) pairs")

print("\n== hook catalog vs wire (the catalog keeps the latest request of a pair)")
bad = 0
for key, (qid, payload, at) in sorted(hook.items()):
    if key not in wire:
        print(f"  ! {key}: in the catalog, never on the wire"); bad += 1; continue
    hits = [w for w in wire[key] if w[1] == qid and w[2] == payload]
    if not hits:
        last = wire[key][-1]
        diff = [k for k in KEYS if last[2].get(k) != payload.get(k)]
        print(f"  ! {key}: no wire request equals the catalog line (ids {sorted({w[1] for w in wire[key]})} vs {qid}; last differs in {diff})"); bad += 1
print(f"  pairs without an identical wire request: {bad} of {len(hook)}")
missing = sorted(k for k in wire if k not in hook)
print(f"  on the wire but not in the catalog: {missing}")

print("\n== within the session")
for key, hits in sorted(wire.items()):
    ids = {h[1] for h in hits}; feats = {json.dumps(h[2].get("features"), sort_keys=True) for h in hits}; togg = {json.dumps(h[2].get("fieldToggles"), sort_keys=True) for h in hits}
    if len(ids) > 1 or len(feats) > 1 or len(togg) > 1:
        print(f"  {key}: {len(hits)} requests, ids {len(ids)}, feature sets {len(feats)}, fieldToggles sets {len(togg)}")
print("  (pairs not listed sent one id, one feature set and one fieldToggles set)")

ph = json.load(open(placeholder_path))
tiad = {e["exports"]["operationName"]: e["exports"] for e in json.loads(subprocess.run(["git", "-C", tiad_dir, "show", "origin/develop:docs/json/GraphQL.json"], capture_output=True, check=True).stdout)}
names = {n for n, _ in wire}
print("\n== placeholder vs this session")
rows = collections.defaultdict(list)
for name, entry in ph.items():
    if not isinstance(entry, dict) or "@path" not in entry:
        continue
    if name not in names:
        rows["not sent in this session"].append(name); continue
    key = (name, entry["@method"]) if (name, entry["@method"]) in wire else next(k for k in wire if k[0] == name)
    at, qid, payload, page = wire[key][-1]
    changes = []
    if key[1] != entry["@method"]:
        changes.append(f"method {entry['@method']} -> {key[1]}")
    if qid != entry["queryId"]:
        changes.append("queryId")
    for k in ["features", "fieldToggles"]:
        old, new = entry.get(k) or {}, payload.get(k) or {}
        add, rem, chg = sorted(set(new) - set(old)), sorted(set(old) - set(new)), sorted(x for x in new if x in old and new[x] != old[x])
        if add or rem or chg:
            changes.append(f"{k} +{len(add)} -{len(rem)} ~{len(chg)}" + (f" [+{','.join(add)}]" if add else "") + (f" [-{','.join(rem)}]" if rem else "") + (f" [~{','.join(f'{x}:{old[x]}->{new[x]}' for x in chg)}]" if chg else ""))
    known = {x.rstrip("?") for x in entry.get("variables", {})}
    newv = sorted(set(payload.get("variables", {})) - known); gone = sorted(x for x in entry.get("variables", {}) if not x.endswith("?") and x not in payload.get("variables", {}))
    if newv or gone:
        changes.append(f"variables new {newv} not sent {gone}")
    t = tiad.get(name, {}).get("queryId")
    tag = "TIAD same as recorded" if t == qid else ("TIAD absent" if t is None else "TIAD OTHER ID")
    rows["changed" if changes else "unchanged"].append(f"{name} [{tag}]" + (": " + "; ".join(changes) if changes else ""))
for title in ["changed", "unchanged", "not sent in this session"]:
    print(f"-- {title}: {len(rows[title])}")
    for r in rows[title]:
        print("   ", r)
print("-- sent in this session, not in the placeholder:", ", ".join(sorted(names - set(ph))))
