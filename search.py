import json
import sqlite3
import argparse
import urllib.request

from gen_db import find_all_components
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
    return parser.parse_args()

def print_decompositions(cur, kanji):
    SQL = "SELECT * FROM decompositions WHERE element = ?"
    decomps = cur.execute(SQL, kanji).fetchall()
    for id, kanji, json_str in decomps:
        json_data = json.loads(json_str)
        print(json.dumps(json_data, indent=2, ensure_ascii=False))

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

def print_combinations(cur, kanji, freq_map, search_anki: bool = False, max: int=20):
    SQL = "SELECT * FROM combinations WHERE component = ?"

    combs = cur.execute(SQL, kanji).fetchall()
    assert len(combs) <= 1
    for _, kanji, json_str in combs:
        json_data = json.loads(json_str)
        for i, kanji in enumerate(json_data):
            sort_value = freq_map.get(kanji, None)
            print_kanji(kanji, freq_map, search_anki and i < max)


        #print(json.dumps(json_data, indent=2, ensure_ascii=False))
    if len(combs) == 0:
        print("Not a part of any other kanji.")

def print_components(cur, kanji):
    SQL = "SELECT * FROM components WHERE kanji = ?"

    combs = cur.execute(SQL, kanji).fetchall()
    for _, kanji, json_str in combs:
        json_data = json.loads(json_str)
        print(" ".join(json_data))

        #print(json.dumps(json_data, indent=2, ensure_ascii=False))
    if len(combs) == 0:
        print("Cannot find components.")



def main():
    args = get_args()

    #with open("kanji_freq/jpdb/kanji_meta_bank_1.json") as f:
    with open("kanji_freq/aozora/kanji_meta_bank_1.json") as f:
        freq_list = json.load(f)
    freq_map = to_freq_map(freq_list)

    with sqlite3.connect("decompositions.db") as conn:
        cur = conn.cursor()
        print_decompositions(cur, args.kanji)
        print()
        print_kanji(args.kanji, freq_map, not args.do_not_search_anki)
        print_components(cur, args.kanji)
        print()
        print_combinations(cur, args.kanji, freq_map, not args.do_not_search_anki, args.max)


if __name__ == "__main__":
    main()
