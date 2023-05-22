import json

def json_to_str(j, indent=None):
    return json.dumps(j, ensure_ascii=False, indent=indent)

ID = 0
ELEMENT = 1
SVG = 2
DECOMPOSITION = 3
COMPONENTS = 4
COMBINATIONS = 5
RANK = 6
OCCURENCES = 7
CUMULATIVE_PERCENT = 8


