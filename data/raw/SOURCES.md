# Sources

Every file here is a public-domain English translation. Nothing here is
copyrighted: these translations are all over 90 years old and out of
copyright in the US.

| File | Text | Translator | Published | Where from |
|---|---|---|---|---|
| `gita_arnold_raw.txt` | Bhagavad Gita ("The Song Celestial") | Sir Edwin Arnold | 1885 | Gutenberg [2388](https://www.gutenberg.org/ebooks/2388) |
| `yogasutras_johnston_raw.txt` | Yoga Sutras of Patanjali | Charles Johnston | 1912 | Gutenberg [2526](https://www.gutenberg.org/ebooks/2526) |
| `upanishads_paramananda_raw.txt` | The Upanishads (includes Isa, Katha, Kena) | Swami Paramananda | 1919 | Gutenberg [3283](https://www.gutenberg.org/ebooks/3283) |
| `arthashastra_shamasastry_raw.txt` | Kautilya's Arthashastra (all 15 books; see below for the ones used) | R. Shamasastry | 1915 | [archive.org](https://archive.org/details/kautilyasarthash00sham) |

Gutenberg files fetched by: `curl -sL https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt`
The Arthashastra: `curl -sL https://archive.org/download/kautilyasarthash00sham/kautilyasarthash00sham_djvu.txt`
(plain curl works on archive.org; it did not on sacred-texts.com).

**Arthashastra: only five chapters are used in the app**, chosen because they
are about justice and procedure, which is what the Nyaya principle needed a
source for: Book I chapters II-IV ("The End of Sciences", including the science
of government by punishment) and XIX ("The Duties of a King"), and Book III
chapter I (judicature: the sources of law, procedure, evidence). The rest (spies,
war, marriage and inheritance law, slaves, and so on) is in the raw file but is
deliberately not ingested: it would put passages into retrieval that have
nothing to do with the questions this app answers. This file is an OCR of a
PDF (page footers like "[Thus ends Chapter I ...]" and OCR errors such as
"Arthasdstra" are present), so `clean.py` strips the footers and the text
keeps the OCR's spelling. Chapter numbers are Shamasastry's, not Kautilya's own
section numbering.

## Verified so far

- `yogasutras_johnston_raw.txt` — Johnston's numbering matches the standard
  one: II.30 is the list of Commandments (non-injury, truthfulness, abstaining
  from stealing, impurity, covetousness) and II.35 is the *effect* of perfected
  non-injury. An earlier version of this note claimed the numbering differed
  (2.35 vs 2.30); that was a mistake: the two numbers are two different
  sutras, not two numberings of one. Contains a Gutenberg typo ("nom injury"
  in II.30).
- `upanishads_paramananda_raw.txt` — contains the full Isa Upanishad, whose
  opening verse (labelled "I") is quoted in `docs/MAPPING.md` section 5. This
  translation labels verses with Roman numerals.
- Every quoted passage in `docs/MAPPING.md` marked "in the corpus" was checked
  verbatim against these three files on 2026-10-11.

## Still needed (not blocking — pick up on a later buffer day)

- **Tirukkural** (G.U. Pope translation) — same problem, needs a manual pull.
- **Mundaka Upanishad** (for the Satya / *satyameva jayate* citation) — this
  Gutenberg edition of the Upanishads doesn't include it; needs a separate
  source (Max Muller's Sacred Books of the East, vol. 15).

Note for `clean.py` (Day 3): `sacred-texts.com` returns a Cloudflare
challenge page to any non-browser request, including this project's own
fetch scripts — don't assume `requests.get()` will work against it later
either.
