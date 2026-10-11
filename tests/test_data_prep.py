import pytest

import chunk
import clean


# ---- references ----

@pytest.mark.parametrize(
    "source, book, sections, verses, expected",
    [
        ("yoga_sutras_johnston", "Book Ii", [None], ["7", "p91", "8"], "Book II, sutras 7-8 with commentary"),
        ("yoga_sutras_johnston", "Book Iii", [None], ["p242", "51", "p243"], "Book III, sutra 51 with commentary"),
        ("yoga_sutras_johnston", "Book I", [None], ["1", "2"], "Book I, sutras 1-2"),
        ("yoga_sutras_johnston", "Book Iv", [None], ["p5", "p6"], "Book IV, commentary"),
        ("yoga_sutras_johnston", None, [None], ["p1"], "Introduction"),
        ("gita_arnold", None, ["Chapter XVIII", "Chapter XVIII"], ["p1", "p2"], "Chapter XVIII"),
        ("gita_arnold", None, ["Chapter III", "Chapter IV"], ["p1", "p2"], "Chapter III to Chapter IV"),
        ("gita_arnold", None, [None, None], ["p1", "p2"], "Introduction"),
        ("upanishads_paramananda", None, ["Katha Upanishad"], ["p9"], "Katha Upanishad"),
        ("arthashastra_shamasastry", "Book III", ["Book III, Chapter I"], ["p52"], "Book III, Chapter I"),
        ("arthashastra_shamasastry", "Book I", ["Book I, Chapter II", "Book I, Chapter III"], ["p1", "p2"],
         "Book I, Chapters II to III"),
    ],
)
def test_build_reference(source, book, sections, verses, expected):
    assert chunk.build_reference(source, book, sections, verses) == expected


def test_a_reference_never_exposes_the_internal_paragraph_counters():
    ref = chunk.build_reference("yoga_sutras_johnston", "Book Ii", [None], ["7", "p91", "8"])
    assert "p91" not in ref


# ---- chunking ----

def record(source, book, verse, text, chapter=None):
    r = {"source": source, "book": book, "verse": verse, "text": text}
    if chapter:
        r["chapter"] = chapter
    return r


def test_chunks_never_span_two_arthashastra_chapters():
    # chapters II and XIX are adjacent in the cleaned data (III-XVIII were not ingested)
    recs = chunk.assign_sections([
        record("arthashastra_shamasastry", "Book I", "p1", "a", "II"),
        record("arthashastra_shamasastry", "Book I", "p2", "b", "II"),
        record("arthashastra_shamasastry", "Book I", "p3", "c", "XIX"),
        record("arthashastra_shamasastry", "Book I", "p4", "d", "XIX"),
    ])
    refs = [c["reference"] for c in chunk.make_chunks(recs)]
    assert refs == ["Book I, Chapter II", "Book I, Chapter XIX"]


def test_chunk_ids_are_unique_and_include_the_book():
    recs = chunk.assign_sections([
        record("yoga_sutras_johnston", "Book I", "1", "x"), record("yoga_sutras_johnston", "Book I", "2", "y"),
        record("yoga_sutras_johnston", "Book Ii", "1", "z"), record("yoga_sutras_johnston", "Book Ii", "2", "w"),
    ])
    ids = [c["chunk_id"] for c in chunk.make_chunks(recs)]
    assert len(ids) == len(set(ids)) == 2  # "1-2" repeats across books; the id must still differ


# ---- Arthashastra cleaning ----

def synthetic_arthashastra():
    """Three books' worth of headings, with every chapter the cleaner is meant
    to keep, plus footers, OCR scraps and all-caps title fragments to drop."""
    body = lambda tag: f"{tag} is a sentence long enough to be kept as a paragraph.\n\n"
    text = "CHAPTER  I.  THE  LIFE  OF  A  KING\n\n" + body("Book one chapter one (dropped)")
    for numeral in ("II", "III", "IV", "XIX"):
        text += f"CHAPTER  {numeral}.  SOMETHING\n\nTITLE FRAGMENT IN CAPS\n\n6m.\n\n" + body(f"B1 {numeral}")
        text += "[Thus  ends  Chapter  X  in  Book  I,  of  the  Arthasdstra  of\nKautilya.]\n\n"
    text += "CHAPTER  V.  NOT  WANTED\n\n" + body("B1 V (dropped)")
    text += "CHAPTER  I.  FORMATION  OF  VILLAGES.\n\n" + body("Book two (dropped)")
    text += "CHAPTER  I.  DETERMINATION  OF  FORMS  OF\n\n" + body("B3 I")
    return text


def test_clean_arthashastra_keeps_only_the_chosen_chapters():
    recs = clean.clean_arthashastra(synthetic_arthashastra())
    assert {(r["book"], r["chapter"]) for r in recs} == {
        ("Book I", "II"), ("Book I", "III"), ("Book I", "IV"), ("Book I", "XIX"), ("Book III", "I"),
    }
    assert all("dropped" not in r["text"] for r in recs)


def test_clean_arthashastra_drops_footers_scraps_and_caps_fragments():
    texts = [r["text"] for r in clean.clean_arthashastra(synthetic_arthashastra())]
    assert not any("Thus ends" in t for t in texts)
    assert "6m." not in texts
    assert "TITLE FRAGMENT IN CAPS" not in texts


def test_clean_arthashastra_collapses_ocr_double_spaces():
    texts = [r["text"] for r in clean.clean_arthashastra(synthetic_arthashastra())]
    assert all("  " not in t for t in texts)


def test_clean_arthashastra_refuses_if_the_book_counting_is_off():
    # Without the Book II / Book III headings the book numbers can't be trusted:
    # better to fail loudly than to label Book II text as Book III.
    with pytest.raises((AssertionError, IndexError)):
        clean.clean_arthashastra("CHAPTER  I.  THE  LIFE  OF  A  KING\n\nSome text that is long enough here.\n")
