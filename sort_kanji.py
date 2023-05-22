"""
outputs frequency map from a sort file. Can optionally sum up all component usages as well,
i.e. a component A is used in B and C, then the frequency of A is freq(A) + freq(B) + freq(C).

- can currently output freq map or occurrence map
"""

import re
import json
import sqlite3
import argparse
from typing import TypedDict, Any, Iterable
from kanji_data import get_kanjivg_data

rx_FREQ_USAGE = re.compile(r"\d+ \((\d+)\)")


# example:
TMP = [
    "奈",
    "宗",
    "尉",
    "斎",
    "款",
    "祀",
    "祁",
    "祇",
    "祓",
    "祕",
    "祗",
    "祚",
    "祟",
    "祠",
    "票",
    "祭",
    "祺",
    "祿",
    "禀",
    "禁",
    "禊",
    "禝",
    "禦",
    "禧",
    "禪",
    "禮",
    "禰",
    "禱",
    "禳",
    "蒜",
    "蒜",
    "隷",
    "隸",
    "頴",
]


class Freq(TypedDict):
    value: int
    displayValue: str


FreqMap = dict[str, Freq]


def sort_kanji(kanjis: Iterable[str], freq_map: FreqMap):
    return sorted(
        kanjis, key=lambda x: 99999999 if x not in freq_map else freq_map[x]["value"]
    )


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sort_file", type=str)
    parser.add_argument("--out-file", type=str, default=None)
    parser.add_argument("--sum-components", action="store_true")
    parser.add_argument("--to-freq-map", action="store_true")
    return parser.parse_args()


def to_freq_map(freq_list: list) -> FreqMap:
    mp = {}
    for entry in freq_list:
        kanji = entry[0]
        freq = entry[2]
        if isinstance(freq, int):
            mp[kanji] = {"value": freq, "displayValue": str(freq)}
        else:
            mp[kanji] = freq

    return mp

def to_occurrence_map(freq_map: FreqMap):
    occurrence_map = {}
    for key, value in freq_map.items():
        result = rx_FREQ_USAGE.match(value["displayValue"])
        if result:
            usage = int(result.group(1))
            occurrence_map[key] = usage
        else:
            print(f'Invalid displayValue: {value["displayValue"]}')
    return occurrence_map


def _create_component_usage_map(
        key: str, cur, usage_map: dict[str, int], component_occurrence_map: dict[str, int], visited: set[str]
):
    # assumption: if in component_occurrence_map, then usage is fully filled
    if key in component_occurrence_map:
        return

    data = get_kanjivg_data(cur, key)
    if data is None:
        return

    if key in visited:
        return # prevents infinite loops, since sometimes components causes infinite loops
    visited.add(key)

    usage = usage_map.get(key, 0)
    for combination in data.combinations:
        #component_occurrence_map[key] += usage_map.get(combination, 0)
        _create_component_usage_map(combination, cur, usage_map, component_occurrence_map, visited)
        if combination in component_occurrence_map:
            usage += component_occurrence_map[combination]
        else:
            print(f"combination not found, using default usage: {combination}")
            usage += usage_map.get(key, 0)
    component_occurrence_map[key] = usage


def create_component_usage_map(usage_map):
    """
    - creates a map that gets sums all frequencies from all combinations

    recursive / dynamic programming
    - traverses to leaves of the tree first
    - only stores when all combinations have values
    - ASSUMPTION: no loops! If there are loops, this may run forever / crash from too much recursion
    """

    with sqlite3.connect("kanjivg.db") as conn:
        cur = conn.cursor()

        visited = set()
        component_occurrence_map = {}
        for key in usage_map:
            # assumption: if in component_occurrence_map, then usage is fully filled
            _create_component_usage_map(key, cur, usage_map, component_occurrence_map, visited)
        return component_occurrence_map
    return {} # shouldn't ever be reached


def to_component_freq_map(freq_map: FreqMap) -> FreqMap:
    # ASSUMPTION: displayValue is always of format `int (int)`,
    # where the 2nd int contains the number of times used

    occurrence_map = to_occurrence_map(freq_map)
    component_occurrence_map = create_component_usage_map(occurrence_map)
    occurrence_list = [(key, usage) for key, usage in component_occurrence_map.items()]
    occurrence_list.sort(key=lambda x: x[1], reverse=True)

    new_freq_map = {}
    for i, (kanji, usage) in enumerate(occurrence_list):
        new_freq_map[kanji] = {"value": i + 1, "displayValue": f"{i+1} ({usage})"}

    return new_freq_map


def main():
    # with open("kanji_freq/kanji_meta_bank_1.json") as f:
    # with open("kanji_freq/aozora/kanji_meta_bank_1.json") as f:
    args = get_args()
    with open(args.sort_file) as f:
        freq_list = json.load(f)
    freq_map = to_freq_map(freq_list)
    if args.sum_components:
        freq_map = to_component_freq_map(freq_map)

    if args.out_file is not None:
        with open(args.out_file, "w") as f:
            if args.to_freq_map:
                json.dump(freq_map, f)
            else:
                json.dump(to_occurrence_map(freq_map), f)

    #sorted_kanji = sort_kanji(TMP, freq_map)
    #for kanji in sorted_kanji:
    #    sort_value = freq_map.get(kanji, None)
    #    print(kanji, sort_value)


if __name__ == "__main__":
    main()
