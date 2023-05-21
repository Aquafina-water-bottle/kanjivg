"""
outputs frequency map from a sort file. Can optionally sum up all component usages as well,
i.e. a component A is used in B and C, then the frequency of A is freq(A) + freq(B) + freq(C).
"""

import re
import json
import sqlite3
import argparse
from typing import TypedDict, Any, Iterable
from kanji_data import get_kanjivg_data

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
  "頴"
]

class Freq(TypedDict):
    value: int
    displayValue: str

FreqMap = dict[str, Freq]


def sort_kanji(kanjis: Iterable[str], freq_map: FreqMap):
    return sorted(kanjis, key=lambda x: 10000 if x not in freq_map else freq_map[x]["value"])

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sort_file", type=str)
    parser.add_argument("--out-file", type=str, default=None)
    parser.add_argument("--sum-components", action="store_true")
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


def to_component_freq_map(freq_map: dict[str, Any]):
    # ASSUMPTION: displayValue is always of format `int (int)`,
    # where the 2nd int contains the number of times used
    rx_FREQ_USAGE = re.compile(r"\d+ \((\d+)\)")
    usage_map = {}
    for key, value in freq_map.items():
        result = rx_FREQ_USAGE.match(value["displayValue"])
        if result:
            usage = int(result.group(1))
            usage_map[key] = usage
        else:
            print(f'Invalid displayValue: {value["displayValue"]}')

    new_usage_map = {}
    with sqlite3.connect("kanjivg.db") as conn:
        cur = conn.cursor()

        for key, value in freq_map.items():
            new_usage_map[key] = usage_map[key]

            data = get_kanjivg_data(cur, key)
            if data is None:
                continue
            for combination in data.combinations:
                new_usage_map[key] += usage_map.get(combination, 0)

    usage_list = [(key, usage) for key, usage in new_usage_map.items()]
    usage_list.sort(key=lambda x: x[1], reverse=True)

    new_freq_map = {}
    for i, (kanji, usage) in enumerate(usage_list):
        new_freq_map[kanji] = {"value": i+1, "displayValue": f"{i+1} ({usage})"}

    return new_freq_map


def main():
    #with open("kanji_freq/kanji_meta_bank_1.json") as f:
    #with open("kanji_freq/aozora/kanji_meta_bank_1.json") as f:
    args = get_args()
    with open(args.sort_file) as f:
        freq_list = json.load(f)
    freq_map = to_freq_map(freq_list)
    if args.sum_components:
        freq_map = to_component_freq_map(freq_map)

    if args.out_file is not None:
        with open(args.out_file, "w") as f:
            json.dump(freq_map, f)

    sorted_kanji = sort_kanji(TMP, freq_map)
    for kanji in sorted_kanji:
        sort_value = freq_map.get(kanji, None)
        print(kanji, sort_value)

if __name__ == "__main__":
    main()


