"""
Confidence-threshold AI tagging for the Traditional Knowledge Repository.

Retrieval-Augmented: a tag is never invented. Every suggestion comes from one of
two places, and the source is recorded with the suggestion so a reviewer can
check it:

  1. RETRIEVED - the item is matched against APPROVED records that already carry
     reviewer-confirmed tags. Each neighbour votes for its own tags, weighted by
     how similar it is. The tag therefore already exists on knowledge a human
     approved, and the evidence names which records voted for it.
  2. VOCABULARY - a controlled vocabulary in Data/tag_vocabulary.json, used when
     there are no approved tagged records to retrieve from (cold start) and as a
     supplement afterwards. Evidence names the terms that matched.

Because those are the only two sources, the set of tags the system is capable of
proposing is bounded and auditable. It cannot produce a tag nobody authorised.

Confidence and handling
  confidence >= HIGH_CONFIDENCE    -> "suggested"    shown to the reviewer pre-ticked
  confidence >= REVIEW_CONFIDENCE  -> "needs_review" shown to the reviewer unticked
  below REVIEW_CONFIDENCE          -> discarded, never shown

No band auto-applies a tag. Nothing written here reaches the repository: tagging
suggestions are written to AIOutput/tags/ as a separate store, and a tag only
becomes real when a reviewer confirms it at the approval step. This follows the
same rule as the rest of the pipeline, that AIOutput/pending/ is never mutated,
so the raw machine output stays separable from human decisions.

What the confidence number is, and is not
  It measures agreement: how strongly similar approved material, or the
  controlled vocabulary, points at this tag. It is NOT a judgement that the tag
  is culturally correct, and it is not a truth score. Only the reviewer decides
  that. See TAGGING.md.

Run:
  python Models/tagging.py --all                  # tag everything pending
  python Models/tagging.py --id <record-id>       # tag one pending record
  python Models/tagging.py --text "some text"     # ad hoc, prints suggestions
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path(__file__).resolve().parent.parent
PENDING_DIR = REPO_ROOT / "AIOutput" / "pending"
APPROVED_DIR = REPO_ROOT / "AIOutput" / "approved"
TAGS_DIR = REPO_ROOT / "AIOutput" / "tags"
VOCAB_FILE = REPO_ROOT / "Data" / "tag_vocabulary.json"

# --- confidence bands -------------------------------------------------------
HIGH_CONFIDENCE = 0.55     # pre-ticked for the reviewer
REVIEW_CONFIDENCE = 0.25   # offered to the reviewer, unticked
MAX_SUGGESTIONS = 5        # keep the reviewer's decision small
NEIGHBOURS = 5             # approved records that get to vote


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load_vocabulary() -> list[dict]:
    """Controlled vocabulary. Returns [] if the file is missing or unreadable."""
    try:
        data = json.loads(VOCAB_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for entry in data.get("tags", []):
        name = (entry.get("name") or "").strip()
        if not name:
            continue
        terms = [t.lower() for t in entry.get("terms", []) if t]
        out.append({"name": name, "terms": terms or [name.lower()]})
    return out


def load_tagged_approved() -> list[dict]:
    """Approved records that already carry reviewer-confirmed tags."""
    records = []
    for f in sorted(APPROVED_DIR.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        tags = [t for t in (rec.get("tags") or []) if isinstance(t, str) and t.strip()]
        if tags and rec.get("original_text"):
            rec["tags"] = tags
            records.append(rec)
    return records


def load_pending() -> dict[str, dict]:
    """Every record from the pipeline output, keyed by id."""
    records = {}
    for f in sorted(PENDING_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for rec in data if isinstance(data, list) else [data]:
            if isinstance(rec, dict) and rec.get("id"):
                records[rec["id"]] = rec
    return records


def _citation(rec: dict) -> str:
    src = rec.get("source", {}) or {}
    bits = [b for b in (src.get("author"), src.get("title")) if b]
    return ", ".join(bits) if bits else rec.get("source_file", "Unknown source")


# ---------------------------------------------------------------------------
# the two suggestion sources
# ---------------------------------------------------------------------------
def _retrieved_votes(text: str, neighbours: list[dict], k: int = NEIGHBOURS) -> dict:
    """Weighted vote over tags held by the most similar approved records.

    Each neighbour contributes its similarity score to every tag it carries.
    Confidence is the tag's share of the total vote, so a tag agreed on by
    several close neighbours scores higher than one seen on a single weak match.
    """
    if not neighbours:
        return {}

    corpus = [n["original_text"] for n in neighbours]
    try:
        vectoriser = TfidfVectorizer(stop_words="english")
        matrix = vectoriser.fit_transform(corpus)
        sims = cosine_similarity(vectoriser.transform([text]), matrix)[0]
    except ValueError:
        return {}   # empty vocabulary after stop-word removal

    ranked = sorted(enumerate(sims), key=lambda p: p[1], reverse=True)[:k]
    ranked = [(i, float(s)) for i, s in ranked if s > 0]
    if not ranked:
        return {}

    total = sum(s for _, s in ranked)
    votes: dict[str, dict] = {}
    for i, sim in ranked:
        rec = neighbours[i]
        for tag in rec["tags"]:
            v = votes.setdefault(tag, {"weight": 0.0, "evidence": []})
            v["weight"] += sim
            v["evidence"].append({
                "record_id": rec.get("id"),
                "citation": _citation(rec),
                "similarity": round(sim, 3),
            })

    for tag, v in votes.items():
        v["confidence"] = round(v["weight"] / total, 3) if total else 0.0
        v["source"] = "retrieved"
        v["evidence"] = sorted(v["evidence"], key=lambda e: -e["similarity"])[:3]
    return votes


def _vocabulary_votes(text: str, vocabulary: list[dict]) -> dict:
    """Match the controlled vocabulary against the text.

    Confidence rises with the number of distinct vocabulary terms matched, since
    one passing mention is weaker evidence than several related terms. It is
    capped below HIGH_CONFIDENCE: a keyword match alone never arrives pre-ticked,
    because matching a word is not the same as the item being about that subject.
    """
    low = (text or "").lower()
    votes = {}
    for entry in vocabulary:
        matched = [t for t in entry["terms"] if t in low]
        if not matched:
            continue
        # 1 term -> 0.20, 2 -> 0.32, 3 -> 0.41, 4 -> 0.48, capped at 0.50
        confidence = min(0.50, 0.20 + 0.12 * (len(matched) - 1) ** 0.85)
        votes[entry["name"]] = {
            "confidence": round(confidence, 3),
            "source": "vocabulary",
            "evidence": [{"matched_terms": sorted(set(matched))[:6]}],
        }
    return votes


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------
def suggest_tags(text: str,
                 high: float = HIGH_CONFIDENCE,
                 review: float = REVIEW_CONFIDENCE,
                 limit: int = MAX_SUGGESTIONS) -> list[dict]:
    """Suggest tags for a piece of text. Never applies them.

    Returns a list, highest confidence first, each item shaped:
      {tag, confidence, status, source, evidence}
    status is "suggested" at or above `high`, "needs_review" at or above
    `review`. Anything below `review` is discarded and not returned at all.
    """
    text = (text or "").strip()
    if not text:
        return []

    votes = _vocabulary_votes(text, load_vocabulary())

    # retrieved evidence is stronger than a keyword match, so it wins on overlap
    for tag, v in _retrieved_votes(text, load_tagged_approved()).items():
        if tag not in votes or v["confidence"] >= votes[tag]["confidence"]:
            votes[tag] = v

    out = []
    for tag, v in votes.items():
        conf = v["confidence"]
        if conf < review:
            continue
        out.append({
            "tag": tag,
            "confidence": conf,
            "status": "suggested" if conf >= high else "needs_review",
            "source": v["source"],
            "evidence": v["evidence"],
        })

    out.sort(key=lambda s: (-s["confidence"], s["tag"]))
    return out[:limit]


def tag_record(rec: dict) -> dict:
    """Produce the suggestion document for one pipeline record."""
    text = rec.get("original_text") or rec.get("summary") or ""
    suggestions = suggest_tags(text)
    return {
        "record_id": rec.get("id"),
        "source_file": rec.get("source_file"),
        "suggestions": suggestions,
        "high_confidence_threshold": HIGH_CONFIDENCE,
        "review_confidence_threshold": REVIEW_CONFIDENCE,
        # explicit, so no downstream component assumes these are applied tags
        "applied": False,
        "requires_human_review": True,
        "tagged_at": datetime.now(timezone.utc).isoformat(),
    }


def write_suggestions(doc: dict) -> Path:
    """Write to AIOutput/tags/. Pending records are never mutated."""
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    path = TAGS_DIR / f"{doc['record_id']}.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def suggestions_for(record_id: str) -> dict | None:
    """Read back previously written suggestions for a record."""
    path = TAGS_DIR / f"{record_id}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print(doc: dict) -> None:
    sug = doc["suggestions"]
    print(f"\n{doc.get('record_id') or 'ad hoc'}  ({doc.get('source_file') or '-'})")
    if not sug:
        print("  no tag reaches the review threshold - nothing suggested")
        return
    for s in sug:
        mark = "*" if s["status"] == "suggested" else " "
        print(f"  {mark} {s['confidence']:.2f}  {s['tag']}  [{s['source']}]")
        for e in s["evidence"]:
            if "matched_terms" in e:
                print(f"        terms: {', '.join(e['matched_terms'])}")
            else:
                print(f"        from {e['citation']} (sim {e['similarity']})")
    print("  * = pre-ticked for the reviewer. Nothing is applied automatically.")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Confidence-threshold tag suggestions (RAG).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="tag every pending record")
    g.add_argument("--id", help="tag one pending record by id")
    g.add_argument("--text", help="tag an ad hoc string, print only")
    ap.add_argument("--dry-run", action="store_true", help="print without writing")
    args = ap.parse_args()

    if args.text:
        _print({"record_id": None, "source_file": None,
                "suggestions": suggest_tags(args.text)})
        return

    pending = load_pending()
    if args.id:
        rec = pending.get(args.id)
        if rec is None:
            raise SystemExit(f"no pending record with id {args.id}")
        targets = [rec]
    else:
        targets = list(pending.values())

    if not targets:
        print("nothing pending to tag")
        return

    tagged_approved = len(load_tagged_approved())
    if tagged_approved == 0:
        print("note: no approved record carries tags yet, so suggestions come from "
              "the controlled vocabulary only (cold start).")

    for rec in targets:
        doc = tag_record(rec)
        if not args.dry_run:
            write_suggestions(doc)
        _print(doc)

    print(f"\n{len(targets)} record(s) processed"
          f"{' (dry run, nothing written)' if args.dry_run else f' -> {TAGS_DIR}'}")


if __name__ == "__main__":
    main()
