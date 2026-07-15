#!/usr/bin/env python3
"""Headless AnkiWeb sync + learned-vocab export.

Logs into AnkiWeb the same way the Anki apps do, syncs the collection
(no GUI needed), then writes every graduated ("review") word in DECK
to OUTPUT, one word per line. Designed to run on a schedule in GitHub
Actions, so your phone reviews reach the list without a laptop.

Required env vars: ANKIWEB_USERNAME, ANKIWEB_PASSWORD
Optional env vars: DECK, FIELD, OUTPUT, COLLECTION_PATH
"""

import os
import re
import sys
from pathlib import Path

import anki.lang

anki.lang.set_lang("en_US")  # init i18n backend; strip_html needs it headless

from anki.collection import Collection
from anki.utils import strip_html

# Bracket furigana like 食[た]べる
BRACKET_READINGS = re.compile(r"\s?\[[^\]]*\]")
# Hiragana, katakana (incl. halfwidth + 々), and kanji
JAPANESE_CHARS = re.compile(
    r"[\u3005\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9d]"
)


def clean(raw: str) -> str:
    text = BRACKET_READINGS.sub("", strip_html(raw))
    return text.replace("\u00a0", " ").strip()


def export_words(col: Collection, deck: str, field: str, output: Path) -> int:
    words: list[str] = []
    seen: set[str] = set()
    missing_field = 0

    for nid in col.find_notes(f'deck:"{deck}" is:review'):
        note = col.get_note(nid)
        if field in note:
            raw = note[field]
        else:
            missing_field += 1
            raw = note.fields[0]
        word = clean(raw)
        if word and JAPANESE_CHARS.search(word) and word not in seen:
            seen.add(word)
            words.append(word)

    if not words:
        sys.exit(
            f'No graduated words found for deck "{deck}" -- check the DECK '
            "and FIELD settings; refusing to publish an empty list."
        )
    output.write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"Exported {len(words)} words to {output}")
    if missing_field:
        print(
            f'Warning: {missing_field} notes have no "{field}" field; '
            "their first field was used instead."
        )
    return len(words)


def sync_from_ankiweb(col: Collection, username: str, password: str) -> None:
    auth = col.sync_login(username, password, endpoint=None)
    out = col.sync_collection(auth, sync_media=False)

    if out.new_endpoint:
        # AnkiWeb's server farm redirects fresh clients to another host;
        # everything after this point must talk to that host, or the full
        # download fails with HTTP 400 "missing original size".
        auth.endpoint = out.new_endpoint

    if out.required in (out.FULL_DOWNLOAD, out.FULL_SYNC):
        # First run in a fresh environment: pull the whole collection.
        # (upload=False means the server copy always wins here, which is
        # what we want -- this copy is disposable.)
        print("Full download required, fetching collection from AnkiWeb...")
        col.close_for_full_sync()
        col.full_upload_or_download(auth=auth, server_usn=None, upload=False)
        col.reopen(after_full_sync=True)
    elif out.required == out.FULL_UPLOAD:
        sys.exit(
            "AnkiWeb is asking for a full upload, which this job never does. "
            "Open Anki on one of your devices, sync it manually, then re-run."
        )
    else:
        print("Incremental sync complete.")


def main() -> None:
    username = os.environ["ANKIWEB_USERNAME"]
    password = os.environ["ANKIWEB_PASSWORD"]
    deck = os.environ.get("DECK", "Japanese")
    field = os.environ.get("FIELD", "Expression")
    output = Path(os.environ.get("OUTPUT", "known_words.txt"))
    col_path = Path(
        os.environ.get("COLLECTION_PATH", "collection/collection.anki2")
    )
    col_path.parent.mkdir(parents=True, exist_ok=True)

    col = Collection(str(col_path))
    try:
        sync_from_ankiweb(col, username, password)
        export_words(col, deck, field, output)
    finally:
        col.close()


if __name__ == "__main__":
    main()
