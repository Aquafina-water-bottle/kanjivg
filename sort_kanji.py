import json
from typing import TypedDict, Iterable

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


def main():
    #with open("kanji_freq/kanji_meta_bank_1.json") as f:
    with open("kanji_freq/aozora/kanji_meta_bank_1.json") as f:
        freq_list = json.load(f)
    freq_map = to_freq_map(freq_list)

    sorted_kanji = sort_kanji(TMP, freq_map)
    for kanji in sorted_kanji:
        sort_value = freq_map.get(kanji, None)
        print(kanji, sort_value)

if __name__ == "__main__":
    main()


