"""Strict-validate stored responses and list every field the generated client does not define.

    cd twitter-openapi && uv run python ../tools/validate_recorded.py <dir> [<Operation> ...]   # after tools/build.py (reads dist/)
<dir> is a recording made with wire_tee.mjs (wire.ndjson + wire_responses/), a strict run's cache/ ({raw, type} files,
or raw files next to a .type file) or a directory of raw dumps named <Operation>.<tag>.json (graphql_get.py DUMP_TO). Unlike the harness it does not stop
at the first field, and it also lists the keys the harness's comparison lets through: a model without the field
compares equal to false, [], {} and null. Prints model fields and counts, never content; exits 1 when anything is listed.
"""
import collections, glob, json, os, re, sys
sys.path.insert(0, "test/python")
import test_serialize as ts
import openapi_client as pt
import yaml
from pydantic import ValidationError

src, only = sys.argv[1], set(sys.argv[2:])
spec = yaml.safe_load(open("dist/docs/openapi-3.0.yaml"))["paths"]
MODELS = {p.rsplit("/", 1)[-1]: m["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[-1]
          for p, ms in spec.items() if "/graphql/" in p for m in ms.values()}


def samples():
    """(operation or model name, model, file, raw) of every stored response the spec has a model for."""
    if os.path.exists(f"{src}/wire.ndjson"):
        for line in open(f"{src}/wire.ndjson"):
            e = json.loads(line)
            name = re.search(r"/graphql/[^/]+/([^/?]+)", e["url"]) if e.get("file") else None
            if name and name[1] in MODELS:
                yield name[1], MODELS[name[1]], e["file"], open(f"{src}/{e['file']}", encoding="utf-8").read()
        return
    for f in sorted(glob.glob(f"{src}/*.json")):
        raw, base = open(f, encoding="utf-8").read(), os.path.basename(f)
        d = json.loads(raw)
        if "raw" in d and "type" in d:
            yield d["type"], d["type"], base, d["raw"]
        elif os.path.exists(f + ".type"):  # a cache stored as raw + .type (README, "Offline validation set")
            model = open(f + ".type").read().strip()
            yield model, model, base, raw
        elif base.split(".")[0] in MODELS:
            yield base[:-5], MODELS[base.split(".")[0]], base, raw


def owner(base, key):
    """Name of the model that holds the last key of a path into the parsed response."""
    obj = base
    try:
        for k in [*key[:-1], None]:
            while not isinstance(obj, list) and obj.__dict__.get("actual_instance") is not None:
                obj = obj.actual_instance  # a oneOf wrapper
            if k is not None:
                obj = obj[k] if isinstance(obj, list) else ts.super_get(obj.__dict__, k)
        return type(obj).__name__
    except Exception as e:
        return f"?{type(e).__name__}"


found = []
def undefined(a, b, base, key):  # replaces the harness's raise: collect and go on
    kind = "absent in the model" if a is None else "absent in the response" if b is None else f"differs ({type(a).__name__} vs {type(b).__name__})"
    found.append(f"{owner(base, key)}.{key[-1]}: {kind}")
    return 0
ts.match_rate_zero = undefined


def let_through(a, b, base, key):
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in b.items():
            if k in a:
                let_through(a[k], v, base, [*key, k])
            elif v is None or v is False or v == [] or v == {}:
                found.append(f"{owner(base, [*key, k])}.{k}: absent in the model, let through as {json.dumps(v)}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i in range(len(a)):
            let_through(a[i], b[i], base, [*key, i])


per_op = collections.defaultdict(lambda: [0, 0]); groups = collections.defaultdict(lambda: collections.defaultdict(set))
for name, model, file, raw in samples():
    if only and name not in only:
        continue
    per_op[name][1] += 1; found.clear()
    try:
        data = getattr(pt, model).from_json(raw)
        rate = ts.match_rate(data.to_dict(), json.loads(raw), data)
        let_through(data.to_dict(), json.loads(raw), data, [])
        if rate == 1 and not found:
            per_op[name][0] += 1
        elif not found:
            groups[name][f"match rate {rate}"].add(file)
        for item in set(found):
            groups[name][item].add(file)
    except ValidationError as e:
        for err in e.errors()[:30]:
            loc = ".".join(str(x) for x in err["loc"] if not isinstance(x, int))
            groups[name][f"validation {loc}: {err['msg'][:90]} (input type {type(err.get('input')).__name__})"].add(file)
    except Exception as e:
        groups[name][f"{type(e).__name__}: {str(e).splitlines()[0][:150]}"].add(file)

print(f"{sum(v[0] for v in per_op.values())}/{sum(v[1] for v in per_op.values())} responses clean in {len(per_op)} operations")
for name in sorted(groups):
    print(f"{name}: {per_op[name][0]}/{per_op[name][1]} clean")
    for what, files in sorted(groups[name].items()):
        print(f"    {what}  [{len(files)} file(s), e.g. {sorted(files)[0]}]")
sys.exit(1 if groups else 0)
