"""Convert a recorded {name: {@path, @method, queryId, variables, features, fieldToggles}} JSON into the relay NDJSON that update_placeholder.py --relay reads."""
import datetime, json, sys
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")  # the recording is a real frontend request
for name, hit in json.load(open(sys.argv[1])).items():
    payload = {k: hit[k] for k in ["variables", "features", "fieldToggles"] if k in hit}
    req = {"path": hit["@path"].removeprefix("/i/api"), "method": hit["@method"], "recordedAt": stamp}
    if hit["@method"] == "GET":
        req["params"] = {k: json.dumps(v) for k, v in payload.items()}
    else:
        req["data"] = payload
    print(json.dumps(req))
