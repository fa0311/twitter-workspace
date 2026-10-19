"""Draft OpenAPI schemas (twitter-openapi style) from one recorded GraphQL response.

usage: json_to_schema.py <response.json> <OpName>
Prints YAML for <OpName>Response and the nested object schemas, referencing the
existing shared schemas where the shape is the same backend object (Timeline,
TimelineResult, UserResults, User, CommunityResult, Community, ItemResult,
TwitterList, ErrorResponse, TypeName). Required = present in every sample of
the object (one sample for plain objects, all elements for arrays).
"""
import json
import re
import sys

TYPENAMES_FILE = "src/openapi/schemas/typename.yaml"
LIST_KEYS = {"id_str", "name", "member_count", "mode"}
ID_RE = re.compile(r"^[0-9]+$")


def camel(s: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\-]", s) if p)


def typename_enum() -> set[str]:
    try:
        text = open(TYPENAMES_FILE, encoding="utf-8").read()
    except FileNotFoundError:
        return set()
    return set(re.findall(r"^\s+([A-Za-z0-9]+),?$", text, re.M))


KNOWN = typename_enum()
unknown_typenames: set[str] = set()
schemas: dict[str, str] = {}


def is_timeline(o) -> bool:
    return isinstance(o, dict) and isinstance(o.get("instructions"), list) and set(o) <= {"instructions", "metadata", "responseObjects"}


def is_timeline_result(o) -> bool:
    return isinstance(o, dict) and set(o) <= {"id", "timeline"} and ("timeline" in o and is_timeline(o["timeline"]))


def wrapped_typename(o):
    if isinstance(o, dict) and set(o) == {"result"} and isinstance(o["result"], dict):
        return o["result"].get("__typename")


def shared_ref(key: str, o):
    """A $ref for shapes that are the same backend object as an existing schema."""
    if is_timeline(o):
        return "./../schemas/timeline.yaml#/components/schemas/Timeline"
    if is_timeline_result(o):
        return "./../schemas/timeline.yaml#/components/schemas/TimelineResult"
    tn = wrapped_typename(o)
    if tn in ("User", "UserUnavailable"):
        return "./../schemas/user.yaml#/components/schemas/UserResults"
    if tn in ("Community", "CommunityUnavailable"):
        return "./../schemas/tweet.yaml#/components/schemas/CommunityResult"
    if tn in ("Tweet", "TweetWithVisibilityResults", "TweetTombstone", "TweetUnavailable"):
        return "./../schemas/tweet.yaml#/components/schemas/ItemResult"
    if isinstance(o, dict) and o.get("__typename") == "User":
        return "./../schemas/user.yaml#/components/schemas/User"
    if isinstance(o, dict) and o.get("__typename") == "Community":
        return "./../schemas/tweet.yaml#/components/schemas/Community"
    if isinstance(o, dict) and LIST_KEYS <= set(o):
        return "./../schemas/list.yaml#/components/schemas/TwitterList"
    return None


def merge(samples: list) -> tuple[dict, set]:
    """Union of properties over the samples, required = present in all."""
    keys = set().union(*(s.keys() for s in samples))
    required = set.intersection(*(set(s.keys()) for s in samples)) if samples else set()
    merged = {k: [s[k] for s in samples if k in s] for k in keys}
    return merged, required


def scalar(key: str, values: list) -> list[str]:
    kinds = {type(v).__name__ for v in values}
    nullable = "NoneType" in kinds
    kinds.discard("NoneType")
    lines = []
    if kinds == {"str"}:
        lines.append("type: string")
        if all(ID_RE.match(v) for v in values if v is not None) and (key.endswith("id") or key.endswith("_id") or key.endswith("id_str")):
            lines.append('pattern: "^[0-9]+$"')
    elif kinds == {"bool"}:
        lines.append("type: boolean")
    elif kinds == {"int"}:
        lines.append("type: integer")
    elif kinds <= {"int", "float"} and kinds:
        lines.append("type: number")
    elif not kinds:
        lines.append("type: string # todo: only null seen")
    else:
        lines.append(f"type: string # todo: mixed {sorted(kinds)}")
    if nullable:
        lines.append("nullable: true")
    return lines


def emit(name: str, samples: list[dict], prefix: str) -> str:
    """Emit the schema `name` for the object samples; nested objects get their own schemas."""
    merged, required = merge(samples)
    out = [f"    {name}:"]
    if required:
        out.append("      required:")
        out += [f'        - "{k}"' for k in sorted(required)]
    out.append("      properties:")
    for key in sorted(merged):
        values = merged[key]
        out.append(f"        {key}:")
        ref = next((shared_ref(key, v) for v in values if shared_ref(key, v)), None)
        if key == "__typename":
            tns = sorted({v for v in values if isinstance(v, str)})
            for t in tns:
                if t not in KNOWN:
                    unknown_typenames.add(t)
            out.append(f'          $ref: "./../schemas/typename.yaml#/components/schemas/TypeName" # {", ".join(tns)}')
        elif key == "errors" and isinstance(values[0], list):
            out.append("          type: array")
            out.append("          items:")
            out.append('            $ref: "./../response/error.yaml#/components/schemas/ErrorResponse"')
        elif ref:
            out.append(f'          $ref: "{ref}"')
        elif all(isinstance(v, dict) for v in values):
            if all(len(v) == 0 for v in values):
                out.append("          type: object")
                out.append("          properties: {} # always {}")
            else:
                child = prefix + camel(key)
                out.append(f'          $ref: "#/components/schemas/{child}"')
                schemas[child] = emit(child, values, child)
        elif all(isinstance(v, list) for v in values):
            items = [x for v in values for x in v]
            out.append("          type: array")
            if not items:
                out.append("          items:")
                out.append("            type: object")
                out.append("            properties: {} # always []")
            elif all(isinstance(x, dict) for x in items):
                iref = next((shared_ref(key, x) for x in items if shared_ref(key, x)), None)
                if iref:
                    out.append("          items:")
                    out.append(f'            $ref: "{iref}"')
                elif all(len(x) == 0 for x in items):
                    out.append("          items:")
                    out.append("            type: object")
                    out.append("            properties: {} # always {}")
                else:
                    child = prefix + camel(key)
                    out.append("          items:")
                    out.append(f'            $ref: "#/components/schemas/{child}"')
                    schemas[child] = emit(child, items, child)
            else:
                out.append("          items:")
                out += ["            " + l for l in scalar(key, items)]
        else:
            out += ["          " + l for l in scalar(key, values)]
    return "\n".join(out) + "\n"


def main():
    global shared_ref
    path, op = sys.argv[1], sys.argv[2]
    if "--no-shared" in sys.argv:  # per-site types: only Timeline / TimelineResult / errors / typenames are shared
        orig = shared_ref
        shared_ref = lambda key, o: orig(key, o) if (is_timeline(o) or is_timeline_result(o)) else None
    data = json.load(open(path, encoding="utf-8"))
    root = emit(op if "--bare" in sys.argv else f"{op}Response", [data] if isinstance(data, dict) else data, op)
    print(root)
    for s in schemas.values():
        print(s)
    if unknown_typenames:
        print(f"# typenames missing from typename.yaml: {', '.join(sorted(unknown_typenames))}", file=sys.stderr)


if __name__ == "__main__":
    main()
