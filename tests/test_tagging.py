"""
Tests for Models/tagging.py.

These check the behaviour the project actually promises, not just that the code
runs: that a tag is never invented, that nothing is applied without a human, and
that the confidence bands route suggestions the way the card specifies.

Run:  python -m pytest tests/test_tagging.py -v
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "tagging", str(REPO_ROOT / "Models" / "tagging.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tagging"] = mod
    spec.loader.exec_module(mod)
    return mod


VOCAB = {
    "tags": [
        {"name": "water and waterways",
         "terms": ["water", "waterhole", "soak", "spring", "creek"]},
        {"name": "fire and land management",
         "terms": ["fire", "burning", "cool burn"]},
        {"name": "language",
         "terms": ["language", "dialect", "word"]},
    ]
}


@pytest.fixture
def tagging(tmp_path, monkeypatch):
    """tagging module pointed at an isolated store."""
    mod = _load_module()
    pending = tmp_path / "pending"
    approved = tmp_path / "approved"
    tags = tmp_path / "tags"
    for d in (pending, approved, tags):
        d.mkdir()
    vocab = tmp_path / "tag_vocabulary.json"
    vocab.write_text(json.dumps(VOCAB), encoding="utf-8")

    monkeypatch.setattr(mod, "PENDING_DIR", pending)
    monkeypatch.setattr(mod, "APPROVED_DIR", approved)
    monkeypatch.setattr(mod, "TAGS_DIR", tags)
    monkeypatch.setattr(mod, "VOCAB_FILE", vocab)
    return mod


def _approved(tagging, rec_id, text, tags, title="Approved source"):
    (tagging.APPROVED_DIR / f"{rec_id}.json").write_text(json.dumps({
        "id": rec_id,
        "original_text": text,
        "tags": tags,
        "status": "approved",
        "access": "community",
        "source": {"title": title, "author": "A. Author"},
    }), encoding="utf-8")


def _pending(tagging, filename, records):
    (tagging.PENDING_DIR / filename).write_text(json.dumps(records), encoding="utf-8")


# --- nothing in, nothing out ------------------------------------------------

def test_empty_text_suggests_nothing(tagging):
    assert tagging.suggest_tags("") == []
    assert tagging.suggest_tags("   ") == []


def test_unrelated_text_suggests_nothing(tagging):
    """Below the review threshold the tag is discarded, not returned weakly."""
    assert tagging.suggest_tags("The quarterly budget spreadsheet was circulated.") == []


# --- cold start: vocabulary only --------------------------------------------

def test_cold_start_uses_vocabulary_only(tagging):
    """With no approved tagged records, suggestions come from the vocabulary."""
    out = tagging.suggest_tags("The soak holds water after rain near the creek.")
    assert out, "expected at least one vocabulary suggestion"
    assert {s["source"] for s in out} == {"vocabulary"}
    assert out[0]["tag"] == "water and waterways"


def test_vocabulary_match_is_never_pre_ticked(tagging):
    """A keyword match alone must not arrive pre-ticked for the reviewer."""
    out = tagging.suggest_tags(
        "Water, waterhole, soak, spring and creek are all named here.")
    assert out
    for s in out:
        assert s["confidence"] < tagging.HIGH_CONFIDENCE
        assert s["status"] == "needs_review"


def test_single_passing_mention_is_discarded(tagging):
    """One keyword is not evidence the item is about that subject."""
    assert tagging.suggest_tags("There is water here.") == []


def test_more_matched_terms_raises_confidence(tagging):
    two = tagging.suggest_tags("Water from the soak.")
    four = tagging.suggest_tags("Water from the soak, the spring and the creek.")
    assert two and four
    assert four[0]["confidence"] > two[0]["confidence"]


# --- retrieval vote ---------------------------------------------------------

def test_retrieved_tag_carries_evidence_naming_the_record(tagging):
    _approved(tagging, "rec-1",
              "Cool burn practice reduces fuel load across the grassland.",
              ["fire and land management"], title="Burning practice")

    out = tagging.suggest_tags("Cool burn practice reduces fuel load on grassland.")
    retrieved = [s for s in out if s["source"] == "retrieved"]
    assert retrieved, "expected a retrieved suggestion from the approved record"

    ev = retrieved[0]["evidence"][0]
    assert ev["record_id"] == "rec-1"
    assert "Burning practice" in ev["citation"]
    assert ev["similarity"] > 0


def test_agreement_across_neighbours_outranks_a_single_match(tagging):
    for i in range(3):
        _approved(tagging, f"fire-{i}",
                  "Cool burn and firestick burning manage fuel load on Country.",
                  ["fire and land management"])
    _approved(tagging, "lang-0",
              "Cool burn and firestick burning manage fuel load on Country.",
              ["language"])

    out = tagging.suggest_tags("Firestick burning and cool burn manage fuel load.")
    by_tag = {s["tag"]: s for s in out}
    assert by_tag["fire and land management"]["confidence"] > by_tag["language"]["confidence"]


# --- the hallucination guarantee --------------------------------------------

def test_tags_only_come_from_vocabulary_or_approved_records(tagging):
    _approved(tagging, "rec-1", "Seasonal movement follows the water.",
              ["a reviewer confirmed tag"])

    allowed = {t["name"] for t in VOCAB["tags"]} | {"a reviewer confirmed tag"}
    for text in ["Water in the soak and the spring.",
                 "Seasonal movement follows the water across Country.",
                 "Language, dialect and word lists were recorded.",
                 "Fire, burning and cool burn on the grassland."]:
        for s in tagging.suggest_tags(text):
            assert s["tag"] in allowed, f"invented tag: {s['tag']}"


def test_missing_vocabulary_file_does_not_crash(tagging):
    tagging.VOCAB_FILE.unlink()
    assert tagging.load_vocabulary() == []
    assert tagging.suggest_tags("Water in the soak.") == []


def test_untagged_approved_records_do_not_vote(tagging):
    """An approved record with no tags contributes nothing to retrieval."""
    (tagging.APPROVED_DIR / "untagged.json").write_text(json.dumps({
        "id": "untagged", "original_text": "Cool burn on the grassland.",
        "status": "approved",
    }), encoding="utf-8")
    assert tagging.load_tagged_approved() == []


# --- nothing is applied without a human -------------------------------------

def test_record_document_is_never_marked_applied(tagging):
    doc = tagging.tag_record({
        "id": "p1", "source_file": "paper.pdf",
        "original_text": "Water in the soak and the spring after rain.",
    })
    assert doc["applied"] is False
    assert doc["requires_human_review"] is True
    assert doc["high_confidence_threshold"] == tagging.HIGH_CONFIDENCE
    assert doc["review_confidence_threshold"] == tagging.REVIEW_CONFIDENCE


def test_suggestions_are_written_to_their_own_store(tagging):
    doc = tagging.tag_record({"id": "p1", "original_text": "Water in the soak."})
    path = tagging.write_suggestions(doc)

    assert path.parent == tagging.TAGS_DIR
    assert tagging.suggestions_for("p1")["record_id"] == "p1"
    assert tagging.suggestions_for("nope") is None


def test_pending_records_are_not_mutated(tagging):
    original = [{"id": "p1", "source_file": "paper.pdf",
                 "original_text": "Water in the soak and the spring.",
                 "status": "pending"}]
    _pending(tagging, "paper.json", original)
    before = (tagging.PENDING_DIR / "paper.json").read_text(encoding="utf-8")

    rec = tagging.load_pending()["p1"]
    tagging.write_suggestions(tagging.tag_record(rec))

    after = (tagging.PENDING_DIR / "paper.json").read_text(encoding="utf-8")
    assert before == after, "tagging must not modify the raw pipeline output"


# --- band routing -----------------------------------------------------------

def test_thresholds_route_suggestions_into_the_right_band(tagging):
    _approved(tagging, "rec-1", "Water in the soak and the spring after rain.",
              ["water and waterways"])
    text = "Water in the soak and the spring after rain."

    high = tagging.suggest_tags(text, high=0.0, review=0.0)
    assert high and all(s["status"] == "suggested" for s in high)

    low = tagging.suggest_tags(text, high=1.1, review=0.0)
    assert low and all(s["status"] == "needs_review" for s in low)

    assert tagging.suggest_tags(text, high=1.1, review=1.1) == []


def test_suggestions_are_capped_and_ordered(tagging):
    out = tagging.suggest_tags(
        "Water, soak, spring, creek, fire, burning, cool burn, language, dialect, word.",
        limit=2)
    assert len(out) == 2
    assert out[0]["confidence"] >= out[1]["confidence"]
