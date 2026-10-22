# Confidence-threshold AI tagging (RAG)

Suggests tags for knowledge items, attaches a confidence score to each, and uses
that score to decide how the suggestion is handled in the review workflow. It
never applies a tag.

Pipeline position:

```
Data/ -> ingest -> summarise -> AIOutput/pending/ -> TAG SUGGESTIONS -> HITL review -> AIOutput/approved/
                                                            |                                  |
                                                     AIOutput/tags/                      confirmed tags
                                                                                                |
                                                            <------- feed back as evidence -----+
```

## Running it

```bash
pip install -r requirements.txt

python Models/tagging.py --all                 # tag every pending record
python Models/tagging.py --id <record-id>      # tag one record
python Models/tagging.py --text "some text"    # ad hoc, prints only
python Models/tagging.py --all --dry-run       # print without writing
```

Through the API:

```
GET /api/items/{id}/tags
```

Returns the suggestion document, reading `AIOutput/tags/` if the CLI has already
run and computing on demand if not.

## Where a tag can come from

Two sources, and only two. This is the point of the design.

**Retrieved.** The item is compared against approved records that already carry
reviewer-confirmed tags. The closest records vote for their own tags, weighted by
similarity, and confidence is a tag's share of the total vote. A tag agreed on by
several close records scores higher than one seen on a single weak match. The
evidence records which approved records voted and how similar each was.

**Vocabulary.** A controlled list in `Data/tag_vocabulary.json`, used when no
approved record carries tags yet (cold start) and as a supplement afterwards.
Confidence rises with the number of distinct terms matched. The evidence records
which terms matched.

Because those are the only two sources, the tagger cannot produce a tag that is
not either in the vocabulary or already confirmed by a reviewer on approved
material. The set of possible outputs is bounded and auditable, which is the same
guarantee the extractive summariser and the retrieval layer give.

## Confidence bands

| Confidence | Status | What happens |
|---|---|---|
| 0.55 and above | `suggested` | Shown to the reviewer pre-ticked |
| 0.25 to 0.55 | `needs_review` | Shown to the reviewer unticked |
| Below 0.25 | discarded | Not shown at all |

Thresholds are `HIGH_CONFIDENCE` and `REVIEW_CONFIDENCE` in `Models/tagging.py`
and should be retuned once there is real approved material to measure against.

A vocabulary match is capped at 0.50, deliberately below the pre-tick threshold.
Matching a word is not the same as an item being about that subject, so a keyword
hit alone never arrives pre-ticked. Only retrieved agreement can reach
`suggested`.

No band applies a tag. A single mention of one vocabulary term scores 0.20 and is
dropped rather than offered weakly.

## What the confidence number is, and is not

It measures **agreement**: how strongly similar approved material, or the
controlled vocabulary, points at this tag.

It is **not** a judgement that the tag is culturally correct, and it is not a
truth score. A confidently suggested tag can still be the wrong tag. Only the
reviewer decides. This matters for how the number is described to the client: it
is a triage signal for the reviewer's attention, not a measure of correctness.

## Human review is structural, not a setting

- Suggestions are written to `AIOutput/tags/`, a separate store. The raw pipeline
  output in `AIOutput/pending/` is never mutated, so machine output stays
  separable from human decisions and the audit trail holds.
- Every suggestion document carries `"applied": false` and
  `"requires_human_review": true` explicitly, so no downstream component can
  mistake suggestions for applied tags.
- Tags reach a record only through the `tags` field on the approve request, which
  carries what the **reviewer** confirmed. Confirmed tags then become retrieval
  evidence for later items, so reviewer decisions improve later suggestions. The
  loop is closed by the human, not by the model.

## The controlled vocabulary

`Data/tag_vocabulary.json` is a **placeholder pending community review**. It is
marked as such in the file.

Culturally sensitive categories are deliberately excluded: ceremony, sacred
sites, restricted men's or women's knowledge, burial, initiation. Those
classifications must be made by community authority and must never be inferred by
a machine from text similarity. Adding them to the vocabulary would make the
tagger capable of labelling material as sacred on the strength of a keyword,
which is the opposite of what the access model is for.

## Tested behaviour

```bash
python -m pytest tests/test_tagging.py -v
```

16 tests covering the promises rather than the plumbing:

- Empty and unrelated text produce no suggestions
- A single passing keyword mention is discarded
- Cold start uses the vocabulary only, and never pre-ticks
- More matched terms raise confidence
- A retrieved suggestion carries evidence naming the approved record and its similarity
- Agreement across several neighbours outranks a single match
- Every suggested tag comes from the vocabulary or an approved record, never invented
- An approved record with no tags does not vote
- A missing vocabulary file degrades to no suggestions rather than crashing
- Suggestion documents are never marked applied
- Suggestions are written to their own store
- Pending records are byte-for-byte unchanged after tagging
- The thresholds route suggestions into the right band
- Suggestions are capped and ordered by confidence

## Known limits

- Retrieval is TF-IDF, so it matches wording rather than meaning. Differently
  worded material about the same subject will not retrieve well. Moving to
  sentence embeddings is the same change that `Models/retrieval.py` needs and
  should be done in one piece.
- Cold start is weak by construction. Until reviewers have confirmed tags on
  approved records, every suggestion is a keyword match capped below the
  pre-tick threshold. This is intended, but it means early demos show the
  vocabulary path rather than the retrieval path unless some material is
  approved and tagged first.
- The thresholds are starting values, not measured ones.
- No tag hierarchy or synonyms. "water" and "waterways" are one tag only because
  they are one vocabulary entry.
