# KanjiVG: Kanji Vector Graphics

## Licence

KanjiVG is copyright Ulrich Apel and released under the Creative Commons
Attribution-Share Alike 3.0 licence:

http://creativecommons.org/licenses/by-sa/3.0/

See the file COPYING for more details.

## Documentation

The project's documentation is at https://kanjivg.tagaini.net/.

## Changes to the original project:
- Added a `gen_db.py` file to generate `decompositions.db`
- Added a `search.py` file to search for kanjis within your Anki collection.
- Renamed `kvg-lookup.py` to `kvg_lookup.py`, so it can be imported from other scripts
- Cleaned up some of the existing python scripts so they can be easier read for me personally (`\t` -> 4 spaces, etc.)

Since this was something like a 5 minute project, most things are hard coded,
including the frequency dictionaries used, and word field in Anki.

## Usage
1.  Download frequency dictionaries into `kanji_freq`.

    Expected file structore:

    ```
    kanji_freq
    ├── aozora
    │   ├── [Kanji Frequency] Aozora Bunko.zip
    │   ├── index.json
    │   └── kanji_meta_bank_1.json
    └── jpdb
        ├── [Kanji Frequency] JPDB Kanji.zip
        ├── index.json
        └── kanji_meta_bank_1.json
    ```

    Files downloaded from https://github.com/MarvNC/yomichan-dictionaries#kanji-frequency

2.  Download the latest xml file from https://github.com/KanjiVG/kanjivg/releases
    (looks like `kanjivg-???.xml.gz`), and rename it to `kanjivg.xml`

3.  Run `python3 gen_db.py`
4.  Done (do whatever with the generated database, and you can use `search.py` now)

