# The Mapping

This is the intellectual spine of Viveka: seven categories from classical Indian
ethics and epistemology, each paired with a live problem in AI system design.
The retrieval prompts and the Ethics Scorecard schema are both built from it.

## How to read the citations

Verified on 2026-10-11 against the text files in `data/raw/`. Every principle
below has two lists:

- **In the corpus (checked).** Passages found in the files this project
  actually retrieves from, quoted as they appear there.
- **Outside the corpus (not checked against a text here).** References from
  standard scholarship that are not in `data/raw/`. Where I checked one on the
  web, it says so.

Things worth knowing about the corpus:

- The Gita is Edwin Arnold's 1885 verse translation. It carries no verse
  numbers, so each Gita passage is placed by chapter and matched to the standard
  verse number by content. Arnold also condenses in places.
- The Yoga Sutras are Charles Johnston's 1912 translation. Its numbering
  matches the standard one (II.30 is the list of Commandments, II.35 is the
  effect of non-injury), and it interleaves commentary with the numbered
  sutras.
- The Upanishads are Swami Paramananda's translation of three texts: Isa,
  Katha and Kena. It labels verses with Roman numerals.
- Quotes keep the translators' wording and spelling. Where the Gutenberg file
  has an obvious typo, it is noted.

The "Maps to" paragraphs are this project's own argument for why a principle
applies to AI systems. They are not claims about what the texts say. Where a
"Concept" paragraph goes beyond what the passages show, it is labelled
**Reading used here**.

## What the corpus supports

| Principle | A passage in the corpus? | Strongest in-corpus passage |
|---|---|---|
| Ahimsa | yes | Yoga Sutras II.30, II.35 |
| Satya | yes | Yoga Sutras II.30, II.36 |
| Dharma | yes | Gita, Chapter II and Chapter XVIII |
| **Nyaya** | **no** | none (see section 4) |
| Aparigraha | yes | Yoga Sutras II.30; Isa Upanishad, verse I |
| Seva | yes | Gita, Chapter III (3.19, 3.20, 3.25) |
| Viveka | yes, for the idea | Katha Upanishad |

---

## 1. Ahimsa (अहिंसा) — non-harm

**In the corpus (checked).**
Yoga Sutras II.30 (Johnston): "The Commandments are these: non-injury,
truthfulness, abstaining from stealing, from impurity, from covetousness." (The
file reads "nom injury", a typo.) Non-injury is first. II.31 calls the
Commandments "not limited to any race, place, time or occasion, universal, are the
great obligation." II.35: "Where non-injury is perfected, all enmity ceases in
the presence of him who possesses it."

**Outside the corpus.**
*Ahimsa paramo dharma* ("non-harm is the highest duty") is a phrase from the
Mahabharata's Anushasana Parva. I confirmed that on the web; the verse number
depends on the edition (13.117.37 in one numbering, 13.116.25 in another), so
it is not given as a firm citation. Not checked against a text here.

**Reading used here.** The corpus establishes non-injury as a universal
obligation. Extending it to harm you did not intend, and to weighing harm
before acting, is this project's reading.

**Maps to: non-maleficence / harm reduction.** In AI terms: red-teaming before
deployment, refusing requests whose plausible harm outweighs the plausible
benefit, and treating an unintended failure mode (a biased classifier, a
jailbreak) as still your responsibility. A system passes the Ahimsa check when
its worst realistic failure was actually weighed against its benefit, not just
its best-case demo.

---

## 2. Satya (सत्य) — truthfulness

**In the corpus (checked).**
Yoga Sutras II.30 lists "truthfulness" second. II.34 names "falsehood" among
the transgressions. II.36: "When he is perfected in truth, all acts and their
fruits depend on him." Johnston's commentary on it: "If he who has attained
should say to a man, Become righteous! the man becomes righteous... His word is
not in vain."

**Outside the corpus.**
*Satyameva jayate* ("truth alone triumphs"), India's national motto, is from
Mundaka Upanishad 3.1.6. Confirmed on the web (several sources agree on the
verse); Mundaka is not in the corpus.

**Reading used here.** The corpus passages establish truthfulness as a
Commandment and falsehood as a transgression. Reading Satya as covering what a
system *implies* and not only what it literally states is this project's
extension. An earlier draft of this file claimed "classical commentary pairs
truth with the instruction to speak truth that is also beneficial"; nothing in
the corpus says that, so it was removed.

**Maps to: transparency & honest capability claims.** A model or product
description that overstates what the system can do, a UI that implies more
certainty than the system has, or a "confidence" that isn't calibrated to
actual accuracy: these are Satya failures even when no single sentence is a
literal lie. The check: does the system represent itself accurately to the
person relying on it?

---

## 3. Dharma (धर्म) — right action in context

**In the corpus (checked).**
Gita, Chapter II (Arnold), the passage that corresponds to 2.47-48, matched by
content: "Let right deeds be Thy motive, not the fruit which comes from them.
And live in action!"
Gita, Chapter XVIII, corresponding to 18.47-48: "Better thine own work is,
though done with fault, Than doing others' work, ev'n excellently... Let no
man leave His natural duty, Prince! though it bear blame!"

**Caveat.** In the Gita, one's own duty (*svadharma*) is tied to a person's
social role by birth. This project uses only the abstract point that what is
right depends on the actor's role and context, and does not take on the caste
framing.

**Reading used here.** "Dharma is not a fixed universal rule" is the project's
summary of the svadharma passages.

**Maps to: accountability & context-aware duty.** Who is answerable for a
given decision a system makes, and does the system's notion of "correct
behavior" actually adapt to context the way a real duty would: a medical
diagnosis assistant and a customer-service chatbot don't owe their users the
same thing. A single global "be helpful" instruction, applied identically
everywhere, is a Dharma failure by this standard.

---

## 4. Nyaya (न्याय) — justice, right reasoning

**In the corpus: nothing.** No passage in the current corpus is a source for
Nyaya. The plan was for Kautilya's Arthashastra and the Nyaya Sutras to supply
it; neither was ever ingested (the Arthashastra is a pending manual download,
see `data/raw/SOURCES.md`). So the passages the app tags `nyaya` are keyword
matches on words like "law" or "judge" inside passages about other things, and
an answer that leans on Nyaya has no genuine Nyaya source behind it.

**Outside the corpus.**
Nyaya is one of the six classical schools of Indian philosophy, founded on
Gautama's Nyaya Sutras, concerned with valid means of knowledge (*pramana*) and
sound inference. The Arthashastra treats *danda-niti*, the ruler's duty to
administer justice. Not checked against a text here.

**Reading used here.** The school is about knowledge and inference; in
everyday language the word also means "justice". This project deliberately
uses both senses together. That is a design choice, not a classical doctrine
that justice and reasoning are one thing.

**Maps to: fairness & due process.** Can the reasoning behind an automated
decision actually be inspected (interpretability, not just a plausible
post-hoc explanation), and can the person it affects contest it? A model
that's accurate on average but whose individual decisions can't be traced or
appealed fails Nyaya even if it passes a fairness metric in aggregate.

---

## 5. Aparigraha (अपरिग्रह) — non-possessiveness

**In the corpus (checked).**
Yoga Sutras II.30 lists "from covetousness" fifth and last. (Johnston renders
*aparigraha* as covetousness; "non-possessiveness" is the usual gloss.)
Isa Upanishad, verse I (Paramananda): "All this, whatsoever exists in the
universe, should be covered by the Lord. Having renounced (the unreal), enjoy
(the Real). Do not covet the wealth of any man." Paramananda's commentary adds:
"He who is rich in the knowledge of the Self does not covet external power or
possession."

**Reading used here.** Taking only what a purpose requires and holding nothing
beyond it out of fear or greed is the project's reading of non-covetousness.

**Maps to: data minimization.** Does the system collect, retain, and infer
only what the stated task needs, or does it hoard data "in case it's useful
later"? A feature that requests permissions or logs signals far beyond what
it uses is an Aparigraha failure, independent of whether that data is ever
misused.

---

## 6. Seva (सेवा) — selfless service

**In the corpus (checked).** Gita, Chapter III (Arnold):
- 3.19: "Therefore, thy task prescribed With spirit unattached gladly perform,
  Since in performance of plain duty man Mounts to his highest bliss."
- 3.20: "By works alone Janak and ancient saints reached blessedness! Moreover,
  for the upholding of thy kind, Action thou should'st embrace."
- 3.25: "Even as the unknowing toil, wedded to sense, So let the enlightened
  toil, sense-freed, but set To bring the world deliverance, and its bliss."

**Note.** *Seva* is not the Gita's word. The Gita's ideas here are acting
without attachment to reward (*nishkama karma*) and acting for the good of the
world (*loka-sangraha*). "Selfless service" is a later name this project uses
for them.

**Reading used here.** Service rendered because it is owed rather than as a
transaction, with the welfare of the person served as the point.

**Maps to: human-centered design.** Is the system optimized for the user's
actual underlying goal, or for a proxy metric (engagement, watch time,
click-through) that serves the platform at the user's expense? Dark
patterns and engagement-maximizing recommender systems are the clearest
modern Seva failures.

---

## 7. Viveka (विवेक) — discernment

**In the corpus (checked).** Katha Upanishad (Paramananda):
- "The good is one thing and the pleasant another. These two, having different
  ends, bind a man. It is well with him who chooses the good. He who chooses
  the pleasant misses the true end." (Standard numbering 1.2.1; the numbering is
  from outside the file.)
- "But he who is full of discrimination and whose mind is always controlled,
  his senses are manageable, like the good horses of a driver." (The chariot
  passage, standard numbering 1.3.6.)

**Outside the corpus.**
*Viveka* as the first qualification of a seeker in Advaita Vedanta, and the
*Viveka-Chudamani* ("Crest-Jewel of Discrimination"), which is traditionally
attributed to Adi Shankaracharya. Standard account; not checked against a text
here, and the authorship is a tradition rather than a settled fact.

**Reading used here.** "Knowing the edge of your own competence" is the
project's extension of discrimination between the good and the pleasant.

**Maps to: human oversight & the limits of automation.** Does a human retain
the judgment call in exactly the situations where the stakes or the ambiguity
exceed what the system can reliably weigh? A system with no fallback to human
judgment, deployed on a decision genuinely too ambiguous for it, fails Viveka
regardless of how well it scores on the other six.

---

## Open items

1. **Nyaya has no source in the corpus.** Either ingest the Arthashastra (a
   manual download) or accept it and say so in the app.
2. **Gita and Upanishad verse numbers are not in the corpus text.** The
   Paramananda file labels verses with Roman numerals, which `clean.py`
   currently discards; they could be recovered.
3. **External references are unchecked against texts:** the Mahabharata verse
   number, the Nyaya Sutras, the Arthashastra, the Viveka-Chudamani, Mundaka
   3.1.6 (confirmed on the web only), and the standard Katha numbering.
4. **Whether the app's retrieved passages support the claims the model attaches
   to them** is a separate question this document does not settle.
