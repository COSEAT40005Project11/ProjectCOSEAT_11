"""
API for the Traditional Knowledge Repository (Project UG_COSEAT_11).

Connects the ingestion pipeline's HITL queue to the review frontend, and
handles the approve step that moves a record into the repository.

Stores (all under AIOutput/):
  pending/   one JSON array per source file, written by Models/ingest_pipeline.py
  approved/  one JSON per approved record  <- this is the repository store for now
  rejected/  one JSON per rejected record

A record is "waiting for review" if it is in a pending file and has NOT yet been
approved or rejected. We never mutate the pipeline's pending files; decisions are
recorded by writing to approved/ or rejected/. That keeps the raw ingest output
intact and makes every decision auditable.

Run:
  pip install fastapi uvicorn
  uvicorn API.app:app --reload        # from the repo root
  then open http://127.0.0.1:8000/
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

#Access Control Stuff 
from typing import Literal
from fastapi import Depends
from API.policy import LEVELS, CLEARANCE, can_view,can_decide, ask_level
from API.auth import get_current_user, require_permission, get_user_or_anonymous

from API.auth_routes import router as auth_router
from API.governance import Attribution, Access, review_lock, atomic_write, require_approval_metadata






Level = Literal["public", "community", "restricted", "sacred"]
#STAFF = ("admin", "reviewer", "custodian") #removing for now since permissions replace the function of STAFF
# End of Access Control Stuff
REPO_ROOT = Path(__file__).resolve().parent.parent
PENDING_DIR = REPO_ROOT / "AIOutput" / "pending"
APPROVED_DIR = REPO_ROOT / "AIOutput" / "approved"
REJECTED_DIR = REPO_ROOT / "AIOutput" / "rejected"
FRONTEND_DIR = REPO_ROOT / "FrontEnd"

for d in (PENDING_DIR, APPROVED_DIR, REJECTED_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Traditional Knowledge Repository API", version="0.1.0")
app.include_router(auth_router) #access stuff 

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _decided_ids() -> set[str]:
    ids = set()
    for d in (APPROVED_DIR, REJECTED_DIR):
        for f in d.glob("*.json"):
            ids.add(f.stem)
    return ids


def _all_pending_records() -> dict[str, dict]:
    """Every record from the pipeline output, keyed by id."""
    records = {}
    for f in sorted(PENDING_DIR.glob("*.json")):
        data = _read_json(f) or []
        for rec in data:
            records[rec["id"]] = rec
    return records


def _to_item(rec: dict) -> dict:
    """Map a pipeline record to the shape the review frontend uses."""
    src = rec.get("source", {}) or {}
    cite = src.get("title") or rec.get("source_file", "Unknown source")
    if src.get("author"):
        cite = f"{src['author']} - {cite}"
    return {
        "id": rec["id"],
        "title": src.get("title") or rec.get("source_file", "Untitled"),
        "summary": rec.get("summary", ""),
        "original_text": rec.get("original_text", ""),   # source of truth for the reviewer
        "status": rec.get("status", "pending"),
        # relevance_score is a review signal (how on-topic), not AI answer confidence
        "confidence": rec.get("relevance_score", 0),
        "access": rec.get("access", "community"),
        "source": cite,
        "source_meta": src,
        "source_file": rec.get("source_file"),
        "chunk_index": rec.get("chunk_index"),
        "summary_method": rec.get("summary_method"),
        "reviewed_by": rec.get("reviewed_by"),   # shown as provenance on approved items
        "reviewed_at": rec.get("reviewed_at"),
        "tags": rec.get("tags", []),
        "attribution": {k: (rec.get("attribution") or {}).get(k) for k in ("community", "credit", "language", "permitted_use")},
    }

# Access Control goes here



# ---------------------------------------------------------------------------
# request models
# ---------------------------------------------------------------------------
class ApproveBody(BaseModel):
    reviewed_by: str
    access: Access = "community"       # public | community | restricted | sacred
    summary: str | None = None         # reviewer may correct the summary
    original_text: str | None = None   # reviewer may correct the source text
    tags: list[str] | None = None      # tags the REVIEWER confirmed, not the AI's


class RejectBody(BaseModel):
    reviewed_by: str
    reason: str | None = None


class SubmitBody(BaseModel):
    title: str
    text: str
    access: Level = "community"
    source: str = "Manual submission"


# ---------------------------------------------------------------------------
# endpoints  (the contract the frontend fetches)
# ---------------------------------------------------------------------------
@app.get("/api/pending")
def get_pending(user: dict = Depends(require_permission("knowledge:decide"))):
    decided = _decided_ids()
    items = [_to_item(r) for rid, r in _all_pending_records().items() if rid not in decided]
    # most on-topic first
    items = [i for i in items if can_view(user, i["access"])] # -otherwise it returns any level of knowledge (scared texts can be viewed by any level of clearence)
    records = _all_pending_records()
    for item in items:
        item["attribution"] = records[item["id"]].get("attribution", {})
    items.sort(key=lambda i: i["confidence"], reverse=True)
    return items


@app.get("/api/approved")
def get_approved(user: dict = Depends(get_user_or_anonymous)):
    items = []
    for f in sorted(APPROVED_DIR.glob("*.json")):
        rec = _read_json(f)
        if rec:
            item = _to_item(rec)
            if can_view(user, item["access"]):
                items.append(item)
    return items


@app.get("/api/stats")
def get_stats():
    decided = _decided_ids()
    pending = [rid for rid in _all_pending_records() if rid not in decided]
    return {
        "pending": len(pending),
        "approved": len(list(APPROVED_DIR.glob("*.json"))),
        "rejected": len(list(REJECTED_DIR.glob("*.json"))),
    }


@app.put("/api/items/{item_id}/attribution")
def update_attribution(item_id: str, body: Attribution,
                       user: dict = Depends(require_permission("consent:manage"))):
    with review_lock:
        if item_id in _decided_ids():
            raise HTTPException(409, "Item has already been reviewed")
        for path in sorted(PENDING_DIR.glob("*.json")):
            records = _read_json(path)
            if not isinstance(records, list):
                continue
            for rec in records:
                if rec.get("id") == item_id:
                    if not can_view(user, rec.get("access", "community")) or not can_view(user, body.allowed_access):
                        raise HTTPException(403, "Insufficient clearance")
                    rec["attribution"] = body.model_dump()
                    rec["attribution_updated_by"] = user["sub"]
                    rec["attribution_updated_at"] = datetime.now(timezone.utc).isoformat()
                    atomic_write(path, records)
                    return {"ok": True, "id": item_id}
        raise HTTPException(404, "Item not found in pending queue")


@app.post("/api/items/{item_id}/approve")
def approve(item_id: str, body: ApproveBody, user=Depends(require_permission("knowledge:decide"))):
    with review_lock:
        rec = _all_pending_records().get(item_id)
        if rec is None:
            raise HTTPException(404, "Item not found in pending queue")
        if item_id in _decided_ids():
            raise HTTPException(409, "Item has already been reviewed")
        if not (can_decide(user, rec.get("access", "community")) and can_decide(user, body.access)):
            raise HTTPException(403, "Insufficient clearance")
        require_approval_metadata(rec, body.access)
        rec = dict(rec)
        if body.summary is not None:
            rec["summary"] = body.summary
        if body.original_text is not None:
            rec["original_text"] = body.original_text
        rec["access"] = body.access
        if body.tags is not None:
            rec["tags"] = [t.strip() for t in body.tags if t and t.strip()]
        rec.update(status="approved", reviewed_by=user["sub"],
                   reviewed_at=datetime.now(timezone.utc).isoformat())
        atomic_write(APPROVED_DIR / f"{item_id}.json", rec)
        return {"ok": True, "status": "approved", "id": item_id}


@app.post("/api/submit")
def submit(body: SubmitBody,  user: dict = Depends(require_permission("knowledge:submit"))):
    if not can_view(user, body.access):
        raise HTTPException(403, "insufficenient clearance for this access level")
    """Manual submission (e.g. an elder recording). Goes to the same HITL queue."""
    import uuid
    rec = {
        "id": str(uuid.uuid4()),
        "attribution": {},
        "source": {"title": body.title, "author": "", "year": "", "url": "",
                   "note": body.source},
        "source_file": "manual",
        "chunk_index": 0,
        "original_text": body.text,
        "summary": body.text,              # reviewer summarises/verifies in the queue
        "summary_method": "manual",
        "relevance_score": 1.0,
        "status": "pending",
        "access": body.access,
        "submitted_by": user["sub"],
        "reviewed_by": None,
        "reviewed_at": None,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    (PENDING_DIR / f"manual_{rec['id']}.json").write_text(
        json.dumps([rec], indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "id": rec["id"]}


@app.post("/api/items/{item_id}/reject")
def reject(item_id: str, body: RejectBody, user: dict = Depends(require_permission("knowledge:decide"))):
    with review_lock:
        rec = _all_pending_records().get(item_id)
        if rec is None:
            raise HTTPException(404, "Item not found in pending queue")
        if item_id in _decided_ids():
            raise HTTPException(409, "Item has already been reviewed")
        if not can_decide(user, rec.get("access", "community")):
            raise HTTPException(403, "Insufficient clearance")
        if not (body.reason or "").strip():
            raise HTTPException(422, "Rejection reason is required")
        rec = dict(rec)
        rec.update(status="rejected", reviewed_by=user["sub"],
                   reviewed_at=datetime.now(timezone.utc).isoformat(), reject_reason=body.reason)
        atomic_write(REJECTED_DIR / f"{item_id}.json", rec)
        return {"ok": True, "status": "rejected", "id": item_id}


@app.get("/api/ask")
def ask(q: str, user: dict = Depends(get_user_or_anonymous)):
    """Answer a question from approved records only, with citations, or abstain.
    Generates nothing: returns verbatim source passages so it cannot hallucinate."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "retrieval", str(REPO_ROOT / "Models" / "retrieval.py"))
    retrieval = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retrieval)
    return retrieval.answer(q, viewer_access=ask_level(user))


@app.get("/api/items/{item_id}/tags")
def item_tags(item_id: str, user: dict = Depends(require_permission("knowledge:decide"))):
    """Confidence-scored tag suggestions for a pending item (RAG, never applied).

    Suggestions are read from AIOutput/tags/ if Models/tagging.py has already run,
    otherwise they are computed on demand. Tags only reach a record when the
    reviewer confirms them at the approve step.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tagging", str(REPO_ROOT / "Models" / "tagging.py"))
    tagging = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tagging)

    rec = _all_pending_records().get(item_id)
    if rec is None or item_id in _decided_ids():
        raise HTTPException(404, "Item not found in pending queue")
    if not can_view(user, rec.get("access", "community")):
        raise HTTPException(403, "Insufficient clearance")
    existing = tagging.suggestions_for(item_id)
    if existing:
        return existing

    rec = _all_pending_records().get(item_id)
    if rec is None:
        raise HTTPException(404, "item not found in pending queue")
    return tagging.tag_record(rec)


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


# serve the frontend from the same origin so no CORS setup is needed.
# mounted LAST so it does not shadow the /api and /health routes above.
# The whole FrontEnd folder is served (not just HTML/) so index.html's ../CSS and ../JS links resolve.
@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/HTML/index.html")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
