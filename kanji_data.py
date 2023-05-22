
import json
from typing import Any, Optional
from dataclasses import dataclass

from util import json_to_str, SVG, DECOMPOSITION, COMPONENTS, COMBINATIONS

@dataclass
class KanjiData:
    svg: str
    decomposition: dict[str, Any]
    components: list[str] # in
    combinations: list[str] # out

    occurence: Optional[int] = None
    rank: Optional[int] = None
    cumulative_percent: Optional[float] = None

    def __repr__(self):
        data = {
            "decomposition": self.decomposition,
            "components": self.components,
            "combinations": self.combinations,
        }
        return json_to_str(data)


def get_kanjivg_data(cur, kanji: str) -> KanjiData | None:
    SQL = "SELECT * FROM kanjivg WHERE element = ?"
    data_list = cur.execute(SQL, kanji).fetchall()
    if len(data_list) > 1:
        print(f"Found more than one entry in kanjivg for {kanji}?")
    if len(data_list) == 0:
        return None
    row = data_list[0]
    return row_to_kanjivg_data(row)


def row_to_kanjivg_data(row: list[Any]) -> KanjiData | None:
    return KanjiData(row[SVG], json.loads(row[DECOMPOSITION]), json.loads(row[COMPONENTS]), json.loads(row[COMBINATIONS]))


