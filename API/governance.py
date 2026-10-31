"""Consent and attribution checks for the local JSON prototype."""
import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

review_lock = RLock()  # Prototype: one server process only.
Access = Literal['public', 'community', 'restricted', 'sacred']


class Attribution(BaseModel):
    community: str = Field(default='', max_length=200)
    credit: str = Field(default='', max_length=500)
    language: str = Field(default='', max_length=100)
    consent_status: Literal['unknown', 'pending', 'granted', 'denied', 'withdrawn'] = 'unknown'
    consent_reference: str = Field(default='', max_length=500)
    authority_reference: str = Field(default='', max_length=500)
    permitted_use: str = Field(default='', max_length=1000)
    allowed_access: Access = 'community'


def require_approval_metadata(record: dict, access: str) -> None:
    try:
        meta = Attribution.model_validate(record.get('attribution') or {})
    except ValueError:
        raise HTTPException(422, 'Attribution metadata is invalid')
    required = (meta.community, meta.credit, meta.language, meta.consent_reference,
                meta.authority_reference, meta.permitted_use)
    if meta.consent_status != 'granted' or not all(field.strip() for field in required):
        raise HTTPException(422, 'Approval requires granted consent, attribution, authority and permitted use')
    if meta.allowed_access != access:
        raise HTTPException(422, 'Access must match the recorded consent scope')


def atomic_write(path: Path, value) -> None:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         suffix='.tmp', delete=False) as f:
            temp_path = f.name
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
