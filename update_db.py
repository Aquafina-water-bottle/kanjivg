"""
updates the database with:
- frequencies (occurrence, rank, cumulative_percent)
- sorted combinations

CURRENTLY REQUIRES A FREQUENCY FILE that is of format:
    {
        "kanji": number
    }
known internally as: "freq_map"
"""

import json
import sqlite3
import argparse
from typing import Optional, TypeVar

from util import json_to_str, COMBINATIONS, ELEMENT

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("sort_file", type=str, default=None)
    parser.add_argument("--occurrence-based", action="store_true")
    parser.add_argument("--update-frequencies", action="store_true")
    parser.add_argument("--update-combinations", action="store_true")
    #parser.add_argument("--sort-file", type=str, default=None)
    #parser.add_argument("--sort-file-is-freq-map", action="store_true")
    return parser.parse_args()

T = TypeVar('T')
def sort_kanji(occurrence_based: bool, lst: list[T], access_lambda, occurrence_map) -> list[T]:
    if occurrence_based:
        return list(reversed(sorted(lst, key=lambda x: -1 if access_lambda(x) not in occurrence_map else occurrence_map[access_lambda(x)])))
    return sorted(lst, key=lambda x: 99999999 if access_lambda(x) not in occurrence_map else occurrence_map[access_lambda(x)])

def update_combinations(cur, element: str, combinations: list[str]):
    UPDATE_ROW_SQL = "UPDATE kanjivg SET combinations = ? WHERE element = ?"
    cur.execute(UPDATE_ROW_SQL, (json_to_str(combinations), element))

def update_frequency(cur, element: str, rank: int, occurences: Optional[int], cumulative_percent: Optional[int]):
    UPDATE_ROW_SQL = "UPDATE kanjivg SET (rank, occurrences, cumulative_percent) = (?,?,?) WHERE element = ?"
    cur.execute(UPDATE_ROW_SQL, (rank, occurences, cumulative_percent, element))

def main():
    args = get_args()

    with open(args.sort_file) as f:
        occurrence_map  = json.load(f)

    #if args.sort_file is None:
    #    freq_map = {}
    #else:
    #    with open(args.sort_file) as f:
    #        freq_list = json.load(f)
    #    if args.sort_file_is_freq_map:
    #        freq_map = freq_list
    #    else:
    #        freq_map = to_freq_map(freq_list)

    with sqlite3.connect("kanjivg.db") as conn:
        cur = conn.cursor()

        # ASSUMPTION: can store all this in memory
        # fortunately, this is should only a few MB large
        rows = list(cur.execute("SELECT * from kanjivg").fetchall())
        print(len(rows))

        if args.update_combinations:
            for row in rows:
                combinations = json.loads(row[COMBINATIONS])
                #print(row[ELEMENT], combinations)
                if len(combinations) == 0:
                    continue
                if occurrence_map:
                    combinations = sort_kanji(args.occurrence_based, combinations, lambda x: x, occurrence_map)
                update_combinations(cur, row[ELEMENT], combinations)

        if args.update_frequencies:
            sorted_rows = sort_kanji(args.occurrence_based, rows, lambda x: x[ELEMENT], occurrence_map)
            #sorted_rows = sorted(rows, key=lambda x: 99999999 if x[ELEMENT] not in occurrence_map else occurrence_map[x[ELEMENT]])
            # if occurrence based -> we iterate reversed (largest to smallest)

            complete_sum = sum(occurrence_map.values())
            current_sum = 0
            for i, row in enumerate(sorted_rows):
                element = row[ELEMENT]
                occurences = None
                cumulative_percent = None
                if args.occurrence_based:
                    current_sum += occurrence_map.get(element, 0)
                    occurences = occurrence_map.get(element, 0)
                    cumulative_percent = current_sum / complete_sum * 100
                update_frequency(cur, element, i+1, occurences, cumulative_percent)


if __name__ == "__main__":
    main()


