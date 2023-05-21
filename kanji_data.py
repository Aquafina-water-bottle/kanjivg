
import json
from typing import Any
from dataclasses import dataclass

from util import json_to_str

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


def get_kanjivg_data(cur, kanji) -> KanjiData | None:
    SQL = "SELECT * FROM kanjivg WHERE element = ?"
    data_list = cur.execute(SQL, kanji).fetchall()
    if len(data_list) > 1:
        print(f"Found more than one entry in kanjivg for {kanji}?")
    if len(data_list) == 0:
        return None
    data = data_list[0]
    return KanjiData(json.loads(data[2]), json.loads(data[3]), json.loads(data[4]))

