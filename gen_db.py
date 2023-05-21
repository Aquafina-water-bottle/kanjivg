from kvg_lookup import canonicalId, readXmlFile
from kanjivg import Kanji, StrokeGr, Stroke
from sort_kanji import to_freq_map, sort_kanji
from dataclasses import dataclass

import json
import sqlite3
from typing import Any
from collections import defaultdict

# select * from decompositions where data like '%隷%'


def json_to_str(j, indent=None):
    return json.dumps(j, ensure_ascii=False, indent=indent)

@dataclass
class KanjiData:
    decomposition: dict[str, Any]
    components: list[str] # in
    combinations: list[str] # out

    def __repr__(self):
        data = {
            "decomposition": self.decomposition,
            "components": self.components,
            "combinations": self.combinations,
        }
        return json_to_str(data)


def json_summary(c: Kanji) -> dict[str, Any] | None:
    strokes = c.strokes
    if strokes is not None:
        return json_group_summary(strokes)
        # result["element"] = strokes.element
        # result["groups"] = json_group_summary(strokes)

    return None


def json_group_summary(gr: StrokeGr):

    # ret += gr.element if gr.element is not None and len(gr.element) > 0 else "・"
    result = {}

    if gr.element is not None and len(gr.element) > 0:
        result["element"] = gr.element
    if gr.position:
        result["position"] = gr.position

    childStrokes = [s.stype for s in gr.childs if isinstance(s, Stroke) and s.stype]
    if len(childStrokes):
        result["strokes"] = childStrokes

    result["groups"] = []
    for g in gr.childs:
        if isinstance(g, StrokeGr):
            result["groups"].append(json_group_summary(g))

    return result


def find_xml(kanji_str: str, files) -> dict[str, Any] | None:
    id = canonicalId(kanji_str)
    return find_xml_id(id, files)


def find_xml_id(id, files):
    data = files.get(id, None)
    if data is not None:
        return json_summary(data)
    raise RuntimeError(f"Character {id} ({chr(int(id, 16))}) not found.\n")


def init_table(conn: sqlite3.Connection):
    cur = conn.cursor()

    DROP_TABLE_SQL = "DROP TABLE IF EXISTS kanjivg"
    cur.execute(DROP_TABLE_SQL)

    # decomposition is of type json object
    # components, combinations is of type json array
    # they both can be empty, i.e. {} or []
    # but CANNOT be null
    CREATE_TABLE_SQL = """
        CREATE TABLE kanjivg (
            id integer PRIMARY KEY NOT NULL,
            element text NOT NULL,
            decomposition text NOT NULL,
            components text NOT NULL,
            combinations text NOT NULL
       );
    """
    cur.execute(CREATE_TABLE_SQL)

    CREATE_IDX_SQL = f"""
        CREATE INDEX idx ON kanjivg(element);
    """
    cur.execute(CREATE_IDX_SQL)
    cur.close()



def find_all_components(summary: dict[str, Any], ignore_element: bool=True) -> list[str]:
    # traverses the tree to find the top most "element" values, if they exist
    # currently ignore individual stroke groups

    if not ignore_element:
        element = summary.get("element")
        if element is not None:
            return [element]

    groups = summary.get("groups")
    if groups is None:
        return []

    result = []
    for group in groups:
        group_comps = find_all_components(group, ignore_element=False)
        result.extend(group_comps)
    return result


def main():
    data: dict[str, KanjiData] = {}
    combinations = defaultdict(set)

    INSERT_ROW_SQL = "INSERT INTO kanjivg (element, decomposition, components, combinations) VALUES (?,?,?,?)"

    #with open("kanji_freq/jpdb/kanji_meta_bank_1.json") as f:
    with open("kanji_freq/aozora/kanji_meta_bank_1.json") as f:
        freq_list = json.load(f)
    freq_map = to_freq_map(freq_list)

    with sqlite3.connect("kanjivg.db") as conn:
        init_table(conn)
        cur = conn.cursor()

        files = readXmlFile("./kanjivg.xml")
        for key in files.keys():
            summary = find_xml(key, files)
            if summary is not None:
                element = summary.get("element", None)
                if element is None:
                    print(f"why does {summary} not have a base element")
                    continue

                components = find_all_components(summary)
                for component in components:
                    combinations[component].add(element)

                data[element] = KanjiData(summary, components, [])

        for component, combs in combinations.items():
            if component not in data:
                print(f"component {component} not in original data")
                data[component] = KanjiData({}, [], [])
            sorted_combinations = sort_kanji(combs, freq_map)
            data[component].combinations = sorted_combinations

        for element, kanji_data in data.items():
            assert kanji_data.decomposition is not None
            assert kanji_data.components is not None
            assert kanji_data.combinations is not None
            cur.execute(INSERT_ROW_SQL, (element, json_to_str(kanji_data.decomposition), json_to_str(kanji_data.components), json_to_str(kanji_data.combinations)))

        cur.close()

if __name__ == "__main__":
    main()
