import json
import sqlite3
import argparse
import urllib.request

from kanji_data import get_kanjivg_data
from util import json_to_str
from sort_kanji import to_freq_map


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("kanji", type=str)
    parser.add_argument("-a", "--do-not-search-anki", action="store_true")
    parser.add_argument("-m", "--max", type=int, default=20)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--sort-file", type=str, default="kanji_freq/aozora/kanji_meta_bank_1.json")
    parser.add_argument("--sort-file-is-freq-map", action="store_true")
    return parser.parse_args()

def print_kanji(kanji, freq_map, search_anki: bool):
    MAX_ANKI_RESULTS = 5
    sort_value = freq_map.get(kanji, None)
    display_value = None
    if sort_value is not None:
        display_value = sort_value.get("displayValue")
    print_values = [kanji, display_value]

    if search_anki:
        print_values.append("-")
        words = []
        card_ids = invoke("findCards", query=f"Word:*{kanji}*")
        some_card_ids = sorted(card_ids)[:MAX_ANKI_RESULTS]
        cards_info = invoke("cardsInfo", cards=some_card_ids)
        if cards_info:
            for info in cards_info:
                words.append(info["fields"]["Word"]["value"])
            remaining = len(card_ids) - MAX_ANKI_RESULTS
            print_values.append("　".join(words))
            if remaining > 0:
                print_values.append(f"+{remaining}")
        else:
            print_values.append("Cannot find kanji in collection")
    print(*print_values)

def print_components(components):
    if components:
        print(" ".join(components))
    else:
        print("No components found.")


def print_combinations(combinations, freq_map, search_anki: bool = False, max: int=20):
    for i, kanji in enumerate(combinations):
        print_kanji(kanji, freq_map, search_anki and i < max)

        #print(json.dumps(json_data, indent=2, ensure_ascii=False))
    if len(combinations) == 0:
        print("Not a part of any other kanji.")


def main():
    args = get_args()

    with open(args.sort_file) as f:
        freq_list = json.load(f)
    if args.sort_file_is_freq_map:
        freq_map = freq_list
    else:
        freq_map = to_freq_map(freq_list)

    with sqlite3.connect("kanjivg.db") as conn:
        cur = conn.cursor()
        data = get_kanjivg_data(cur, args.kanji)
        if data is None:
            print("Could not find kanjivg data.")
        else:
            if args.verbose:
                print("decomposition:", json_to_str(data.decomposition, indent=2))
                print()
            print_kanji(args.kanji, freq_map, not args.do_not_search_anki)
            print_components(data.components)
            print()
            print_combinations(data.combinations, freq_map, not args.do_not_search_anki, args.max)


if __name__ == "__main__":
    main()
