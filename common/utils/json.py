from common.types.jsonable import JsonType


def _flatten(json: JsonType) -> dict[str, JsonType]:
    if isinstance(json, dict):
        return {f".{k1}{k2}": v for k1, d in json.items() for k2, v in _flatten(d).items()}
    elif isinstance(json, list):
        return {f"[{i}]{k}": v for i, d in enumerate(json) for k, v in _flatten(d).items()}
    else:
        return {"": json}


def flatten(json: JsonType) -> dict[str, JsonType]:
    if isinstance(json, dict):
        return {f"{k1}{k2}": v for k1, d in json.items() for k2, v in _flatten(d).items()}
    else:
        return _flatten(json)


if __name__ == "__main__":
    import json

    with open("items.json", encoding='utf8') as f:
        data = json.load(f)

    flat = flatten(data)
    print(json.dumps(flat, indent=4))
