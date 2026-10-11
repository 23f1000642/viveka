# Sources

Every file here is a public-domain English translation, pulled from Project
Gutenberg. Nothing here is copyrighted — these translations are all 90+ years
old and out of copyright in the US.

| File | Text | Translator | Published | Gutenberg ID |
|---|---|---|---|---|
| `gita_arnold_raw.txt` | Bhagavad Gita ("The Song Celestial") | Sir Edwin Arnold | 1885 | [2388](https://www.gutenberg.org/ebooks/2388) |
| `yogasutras_johnston_raw.txt` | Yoga Sutras of Patanjali | Charles Johnston | 1912 | [2526](https://www.gutenberg.org/ebooks/2526) |
| `upanishads_paramananda_raw.txt` | The Upanishads (includes Isa, Katha, Kena) | Swami Paramananda | 1919 | [3283](https://www.gutenberg.org/ebooks/3283) |

Fetched by: `curl -sL https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt`

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

- **Arthashastra** (R. Shamasastry translation) — not on Project Gutenberg;
  sacred-texts.com blocks automated fetches (Cloudflare), so this will need a
  manual download from [archive.org](https://archive.org/details/kautilyasarthash00sham)
  or [wisdomlib.org](https://www.wisdomlib.org/hinduism/book/kautilya-arthashastra).
- **Tirukkural** (G.U. Pope translation) — same problem, needs a manual pull.
- **Mundaka Upanishad** (for the Satya / *satyameva jayate* citation) — this
  Gutenberg edition of the Upanishads doesn't include it; needs a separate
  source (Max Muller's Sacred Books of the East, vol. 15).

Note for `clean.py` (Day 3): `sacred-texts.com` returns a Cloudflare
challenge page to any non-browser request, including this project's own
fetch scripts — don't assume `requests.get()` will work against it later
either.
