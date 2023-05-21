import json

def json_to_str(j, indent=None):
    return json.dumps(j, ensure_ascii=False, indent=indent)

