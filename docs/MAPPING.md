# The Mapping

This is the intellectual spine of Viveka: seven categories from classical Indian
ethics and epistemology, each paired with a live problem in AI system design.
The RAG prompts (Week 2) and the Ethics Scorecard schema (Week 3) are both
generated directly from this document, so it needs to be right before either
gets built.

**A note on sourcing.** The verse references below point to well-known passages
in the public domain (composed well over a thousand years ago; even 19th/early
20th-century English translations, such as Kashinath Trimbak Telang's or Edwin
Arnold's Gita, R. Shamasastry's Arthashastra, and James Haughton Woods' Yoga
Sutras, are now out of copyright). The wording here is a paraphrase from memory,
not a verbatim quotation — Day 2's job is to pull the actual translated text
into `data/raw/` and check every reference against it before it's cited in the
app. Treat every citation below as "verify this," not "trust this."

---

## 1. Ahimsa (अहिंसा) — non-harm

**Source.** Listed first among the five *yamas* (ethical restraints) in the
Yoga Sutras of Patanjali (2.30). Also the source of the well-known line from
the Mahabharata's Anushasana Parva, *ahimsa paramo dharma* — "non-harm is the
highest duty."

**The concept.** Ahimsa is not passive non-violence; it's an active
obligation to consider the harm your action could cause before you take it,
extended to harm you didn't intend as much as harm you did.

**Maps to: non-maleficence / harm reduction.** In AI terms — red-teaming
before deployment, refusing requests whose plausible harm outweighs the
plausible benefit, and treating an unintended failure mode (a biased
classifier, a jailbreak) as still your responsibility even though you didn't
intend it. A system passes the Ahimsa check when its worst realistic failure
was actually weighed against its benefit, not just its best-case demo.

---

## 2. Satya (सत्य) — truthfulness

**Source.** The second *yama* (Yoga Sutras 2.30). Also the source of India's
national motto, *satyameva jayate* — "truth alone triumphs" — from the
Mundaka Upanishad (3.1.6).

**The concept.** Satya is truthfulness that accounts for effect, not just
literal accuracy — classical commentary pairs it with the instruction to
speak truth that is also beneficial, not truth wielded to wound.

**Maps to: transparency & honest capability claims.** A model or product
description that overstates what the system can do, a UI that implies more
certainty than the system has, or a "confidence" that isn't calibrated to
actual accuracy — these are Satya failures even when no single sentence is a
literal lie. The check: does the system represent itself accurately to the
person relying on it?

---

## 3. Dharma (धर्म) — right action in context

**Source.** The Bhagavad Gita's central teaching, most famously 2.47
(*karmanye vadhikaraste* — you have a right to your actions, never to their
fruits) and 18.47 (better one's own dharma imperfectly done than another's
performed well — *svadharma*, duty is relative to role and context).

**The concept.** Dharma is not a fixed universal rule; it's the right action
*for this actor, in this context, given this role*. What's dharmic for a
king differs from what's dharmic for a renunciate — the Gita is explicit that
duty is contextual, not one-size-fits-all.

**Maps to: accountability & context-aware duty.** Who is answerable for a
given decision a system makes, and does the system's notion of "correct
behavior" actually adapt to context the way a real duty would — a medical
diagnosis assistant and a customer-service chatbot don't owe their users the
same thing. A single global "be helpful" instruction, applied identically
everywhere, is a Dharma failure by this standard.

---

## 4. Nyaya (न्याय) — justice, right reasoning

**Source.** Nyaya is also the name of one of the six classical schools of
Indian philosophy, founded on Gautama's Nyaya Sutras, concerned with valid
means of knowledge (*pramana*) and sound inference. Kautilya's Arthashastra
separately details *danda-niti* — the ruler's duty to administer impartial
justice.

**The concept.** Nyaya links "justice" and "correct reasoning" as the same
word on purpose: a just outcome is one you can trace back through valid
steps, not one that merely feels fair.

**Maps to: fairness & due process.** Can the reasoning behind an automated
decision actually be inspected (interpretability, not just a plausible
post-hoc explanation), and can the person it affects contest it? A model
that's accurate on average but whose individual decisions can't be traced or
appealed fails Nyaya even if it passes a fairness metric in aggregate.

---

## 5. Aparigraha (अपरिग्रह) — non-possessiveness

**Source.** The fifth and last *yama* (Yoga Sutras 2.30). Echoed in the
opening verse of the Isha Upanishad: enjoy through renunciation; do not covet
what belongs to another.

**The concept.** Aparigraha is the discipline of taking only what a purpose
actually requires and holding nothing beyond that out of fear or greed.

**Maps to: data minimization.** Does the system collect, retain, and infer
only what the stated task needs, or does it hoard data "in case it's useful
later"? A feature that requests permissions or logs signals far beyond what
it uses is an Aparigraha failure, independent of whether that data is ever
misused.

---

## 6. Seva (सेवा) — selfless service

**Source.** The Gita's doctrine of *nishkama karma* — action performed as
duty without attachment to personal reward (3.19) — extended to *loka
sangraha*, holding the welfare of the world together as a reason to act
(3.20, 3.25).

**The concept.** Seva is service rendered because it's owed, not because it's
transactional — the server's welfare is the point, not a side effect of
serving the server.

**Maps to: human-centered design.** Is the system optimized for the user's
actual underlying goal, or for a proxy metric — engagement, watch time,
click-through — that serves the platform at the user's expense? Dark
patterns and engagement-maximizing recommender systems are the clearest
modern Seva failures.

---

## 7. Viveka (विवेक) — discernment

**Source.** Central to Advaita Vedanta; *viveka* (discrimination between the
real and the unreal, the permanent and the impermanent) is named the first
qualification a seeker needs, most famously in the *Viveka-Chudamani*
("Crest-Jewel of Discrimination") attributed to Adi Shankaracharya.

**The concept.** Viveka is the meta-skill of knowing which of your other
faculties applies here, and — critically — knowing the edge of your own
competence.

**Maps to: human oversight & the limits of automation.** Does a human retain
the judgment call in exactly the situations where the stakes or the ambiguity
exceed what the system can reliably weigh? A system with no fallback to human
judgment, deployed on a decision genuinely too ambiguous for it, fails Viveka
regardless of how well it scores on the other six.

---

## Next

Day 2: pull the actual public-domain translations into `data/raw/` and
replace every paraphrase above with a checked citation (chapter and verse,
translator, and a short direct quote).
