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

- `yogasutras_johnston_raw.txt` — confirms the *ahimsa* (non-injury) passage
  used in `docs/MAPPING.md` §1, though Johnston's numbering marks its effects
  at sutra 2.35, not 2.30 (translators number the Yamas' *listing* vs. their
  *elaboration* differently — needs a second translation cross-checked before
  the final citation goes in the app).
- `upanishads_paramananda_raw.txt` — contains the full Isa-Upanishad, needed
  for the Aparigraha citation in `docs/MAPPING.md` §5.

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
