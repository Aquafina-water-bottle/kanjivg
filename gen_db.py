from kvg_lookup import canonicalId, readXmlFile
from kanjivg import Kanji, StrokeGr, Stroke
from util import json_to_str
from utils import listSvgFiles, SvgFileInfo
from kanji_data import KanjiData


import json
import sqlite3
from typing import Any
from collections import defaultdict

# select * from decompositions where data like '%隷%'


def json_summary(c: Kanji) -> dict[str, Any] | None:
    strokes = c.strokes
    if strokes is not None:
        return json_group_summary(strokes)
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

def find_svg_id(id, all_svg_files: list[SvgFileInfo]) -> SvgFileInfo:
    # finds first file that isn't a variant
    svg_files = [f for f in all_svg_files if f.id == id]
    for svg_file in svg_files:
        if not hasattr(svg_file, "variant"): # non-variant
            return svg_file
        #(f.path, f.read())
    #if len(svg_files) == 0:
    #    return None
    return svg_files[0]


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
            svg text NOT NULL,
            decomposition text NOT NULL,
            components text NOT NULL,
            combinations text NOT NULL,
            rank integer,
            occurrences integer,
            cumulative_percent real
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


def override_data(data):
    OVERRIDE_FILE = "custom.json"
    with open(OVERRIDE_FILE) as f:
        json_data = json.load(f)
    for key, value in json_data.items():
        for column, col_val in value.items():
            if column == "combinations":
                data[key].combinations.extend(col_val)
            else:
                setattr(data[key], column, col_val)




def main():
    data: dict[str, KanjiData] = {}
    combinations = defaultdict(set)

    INSERT_ROW_SQL = "INSERT INTO kanjivg (element, svg, decomposition, components, combinations) VALUES (?,?,?,?,?)"

    # parse gigantic xml file containing all kanjis into summary and components
    files = readXmlFile("./kanjivg.xml")
    all_svg_files = listSvgFiles("./kanji/")
    for key in files.keys():
        id = canonicalId(key)
        summary = find_xml_id(id, files)
        svg_file = find_svg_id(id, all_svg_files)
        with open(svg_file.path) as f:
            svg_file_contents = f.read()
        if summary is not None:
            element = summary.get("element", None)
            if element is None:
                print(f"why does {summary} not have a base element")
                continue

            components = find_all_components(summary)
            # backfills combinations
            for component in components:
                combinations[component].add(element)

            data[element] = KanjiData(svg_file_contents, summary, components, [])

    # sets combinations for each kanji
    for component, combs in combinations.items():
        if component not in data:
            print(f"component {component} not in original data")
            data[component] = KanjiData("", {}, [], [])
        if component in combs:
            combs.remove(component) # so it doesn't repeat itself
        #data[component].combinations = sort_kanji(combs, freq_map) if freq_map else list(combs)
        data[component].combinations = list(combs)

    # reads custom.json to override any specific entries
    override_data(data)

    with sqlite3.connect("kanjivg.db") as conn:
        init_table(conn)
        cur = conn.cursor()

        for element, kanji_data in data.items():
            assert kanji_data.decomposition is not None
            assert kanji_data.components is not None
            assert kanji_data.combinations is not None
            cur.execute(INSERT_ROW_SQL, (element, kanji_data.svg, json_to_str(kanji_data.decomposition), json_to_str(kanji_data.components), json_to_str(kanji_data.combinations)))

        cur.close()

if __name__ == "__main__":
    main()
