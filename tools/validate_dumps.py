"""Strict-validate dumped GraphQL responses against the generated Python models (same comparison as the live harness).

    uv run python /root/workspace/tools/validate_dumps.py CreateList=ListResponse DeleteList=DeleteListResponse ...   # from a twitter-openapi checkout
Each argument is <dump name>=<response model>; dumps are read from /root/workspace/tools/out/responses/<name>.json or a path given as name.
"""
import json, os, sys
os.environ["STRICT_MODE"] = "True"
sys.path.insert(0, "test/python")
import test_serialize as ts
import openapi_client as pt
ok = True
for arg in sys.argv[1:]:
    name, model = arg.rsplit("=", 1)
    path = name if os.path.exists(name) else f"/root/workspace/tools/out/responses/{name}.json"
    raw = open(path, encoding="utf-8").read()
    try:
        data = pt.__dict__[model].from_json(raw)
        rate = ts.match_rate(data.to_dict(), json.loads(raw), data)
        print(f"{name:34s} {model:34s} match {rate}")
    except Exception as e:
        ok = False
        print(f"{name:34s} {model:34s} FAIL {type(e).__name__}: {str(e).splitlines()[0][:160]}")
sys.exit(0 if ok else 1)
