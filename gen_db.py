from kvg_lookup import canonicalId, readXmlFile
from kanjivg import Kanji, StrokeGr, Stroke
from sort_kanji import to_freq_map, sort_kanji

import json
import sqlite3
from typing import Any
from collections import defaultdict

# select * from decompositions where data like '%隷%'

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


def init_decomps_table(conn: sqlite3.Connection):
    cur = conn.cursor()

    DROP_TABLE_SQL = "DROP TABLE IF EXISTS decompositions"
    cur.execute(DROP_TABLE_SQL)

    CREATE_TABLE_SQL = """
        CREATE TABLE decompositions (
            id integer PRIMARY KEY NOT NULL,
            element text NOT NULL,
            data text NOT NULL
       );
    """
    cur.execute(CREATE_TABLE_SQL)

    CREATE_IDX_SQL = f"""
        CREATE INDEX idx ON decompositions(element);
    """
    cur.execute(CREATE_IDX_SQL)
    cur.close()


def init_combinations_table(conn: sqlite3.Connection):
    cur = conn.cursor()

    DROP_TABLE_SQL = "DROP TABLE IF EXISTS combinations"
    cur.execute(DROP_TABLE_SQL)

    CREATE_TABLE_SQL = """
        CREATE TABLE combinations (
            id integer PRIMARY KEY NOT NULL,
            component text NOT NULL,
            data text NOT NULL
       );
    """
    cur.execute(CREATE_TABLE_SQL)

    CREATE_IDX_SQL = f"""
        CREATE INDEX idx2 ON combinations(component);
    """
    cur.execute(CREATE_IDX_SQL)
    cur.close()


def init_components_table(conn: sqlite3.Connection):
    cur = conn.cursor()

    DROP_TABLE_SQL = "DROP TABLE IF EXISTS components"
    cur.execute(DROP_TABLE_SQL)

    CREATE_TABLE_SQL = """
        CREATE TABLE components (
            id integer PRIMARY KEY NOT NULL,
            kanji text NOT NULL,
            data text NOT NULL
       );
    """
    cur.execute(CREATE_TABLE_SQL)

    CREATE_IDX_SQL = f"""
        CREATE INDEX idx3 ON components(kanji);
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
    INSERT_ROW_SQL = "INSERT INTO decompositions (element, data) VALUES (?,?)"
    INSERT_ROW2_SQL = "INSERT INTO combinations (component, data) VALUES (?,?)"
    INSERT_ROW3_SQL = "INSERT INTO components (kanji, data) VALUES (?,?)"
    combinations = defaultdict(list)

    #with open("kanji_freq/jpdb/kanji_meta_bank_1.json") as f:
    with open("kanji_freq/aozora/kanji_meta_bank_1.json") as f:
        freq_list = json.load(f)
    freq_map = to_freq_map(freq_list)

    with sqlite3.connect("decompositions.db") as conn:
        init_decomps_table(conn)
        init_combinations_table(conn)
        init_components_table(conn)
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
                    combinations[component].append(element)

                cur.execute(INSERT_ROW_SQL, (element, json.dumps(summary, ensure_ascii=False)))
                cur.execute(INSERT_ROW3_SQL, (element, json.dumps(components, ensure_ascii=False)))

        for component, combs in combinations.items():
            sorted_combs = sort_kanji(combs, freq_map)
            cur.execute(INSERT_ROW2_SQL, (component, json.dumps(sorted_combs, ensure_ascii=False)))

        cur.close()

    # summary = find_xml("夜", files)
    #summary = find_xml("栗", files)
    #print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
