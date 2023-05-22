rm -rf ./kanjivg.db

python3 kvg.py release
python3 gen_db.py

python3 sort_kanji.py kanji_freq/innocent_corpus/kanji_meta_bank_1.json --out-file kanji_freq/innocent_corpus/kanji_component_freq.json --sum-components
python3 sort_kanji.py kanji_freq/innocent_corpus/kanji_meta_bank_1.json --out-file kanji_freq/innocent_corpus/kanji_occurrence_freq.json
python3 sort_kanji.py kanji_freq/innocent_corpus/kanji_meta_bank_1.json --out-file kanji_freq/innocent_corpus/kanji_component_freq_map.json --sum-components --to-freq-map

python3 update_db.py --update-frequencies kanji_freq/innocent_corpus/kanji_occurrence_freq.json --occurrence-based
python3 update_db.py --update-combinations kanji_freq/innocent_corpus/kanji_component_freq.json --occurrence-based
