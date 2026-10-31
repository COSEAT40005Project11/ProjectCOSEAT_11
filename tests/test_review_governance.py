"""Review integration tests use temporary storage and local JWT test accounts."""
import json
import os
os.environ.setdefault('JWT_SECRET', 'test-only-secret-' + 'x' * 80)
os.environ['DEV_SEED_USERS'] = '1'

import pytest
from fastapi.testclient import TestClient
import API.app as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    for attr in ('PENDING_DIR', 'APPROVED_DIR', 'REJECTED_DIR'):
        folder = tmp_path / attr
        folder.mkdir()
        monkeypatch.setattr(api, attr, folder)
    return TestClient(api.app)


def auth(client, role):
    result = client.post('/auth/login', data={'username': f'{role}@test.local', 'password': 'password1234'})
    assert result.status_code == 200
    return {'Authorization': 'Bearer ' + result.json()['access_token']}


def submit(client, headers, access='public'):
    r = client.post('/api/submit', headers=headers, json={'title': 'Synthetic rainfall',
                    'text': 'Fictional seasonal rainfall and fishing.', 'access': access})
    assert r.status_code == 200
    return r.json()['id']


META = {'community': 'Fictional community', 'credit': 'Fictional contributor',
        'language': 'English', 'consent_status': 'granted', 'consent_reference': 'DEMO-001',
        'authority_reference': 'DEMO-002', 'permitted_use': 'Classroom demonstration',
        'allowed_access': 'public'}


def test_review_workflow_and_identity(client):
    admin = auth(client, 'admin')
    rid = submit(client, admin)
    url = f'/api/items/{rid}'
    body = {'reviewed_by': 'forged', 'access': 'public', 'tags': ['seasonal knowledge']}
    assert client.get('/api/pending').status_code == 401
    assert client.get(url + '/tags').status_code == 401
    assert client.post(url + '/approve', headers=admin, json=body).status_code == 422
    assert client.put(url + '/attribution', headers=admin, json=META).status_code == 200
    assert client.post(url + '/approve', headers=admin, json=body).status_code == 200
    assert client.post(url + '/approve', headers=admin, json=body).status_code == 409
    assert client.post(url + '/reject', headers=admin, json={'reviewed_by': 'x', 'reason': 'again'}).status_code == 409
    approved = client.get('/api/approved').json()[0]
    assert approved['reviewed_by'] != 'forged'
    assert approved['tags'] == ['seasonal knowledge']
    assert approved['attribution']['credit'] == META['credit']
    assert 'consent_reference' not in approved['attribution']
    assert client.get('/api/pending', headers=admin).json() == []


def test_consent_manager_and_access_scope(client):
    admin = auth(client, 'admin')
    reviewer = auth(client, 'reviewer')
    rid = submit(client, admin)
    url = f'/api/items/{rid}'
    assert client.put(url + '/attribution', headers=reviewer, json=META).status_code == 403
    assert client.put(url + '/attribution', headers=admin, json={**META, 'consent_status': 'withdrawn'}).status_code == 200
    assert client.post(url + '/approve', headers=reviewer, json={'reviewed_by': 'x', 'access': 'public'}).status_code == 422
    assert client.put(url + '/attribution', headers=admin, json=META).status_code == 200
    assert client.post(url + '/approve', headers=reviewer, json={'reviewed_by': 'x', 'access': 'community'}).status_code == 422
    assert client.post(url + '/approve', headers=reviewer, json={'reviewed_by': 'x', 'access': 'invalid'}).status_code == 422


def test_reject_reason_and_clearance(client):
    admin = auth(client, 'admin')
    reviewer = auth(client, 'reviewer')
    rid = submit(client, admin, access='sacred')
    url = f'/api/items/{rid}'
    assert client.get(url + '/tags', headers=reviewer).status_code == 403
    assert client.post(url + '/reject', headers=reviewer, json={'reviewed_by': 'x', 'reason': 'test'}).status_code == 403
    assert client.post(url + '/reject', headers=admin, json={'reviewed_by': 'x', 'reason': ''}).status_code == 422
    assert client.post(url + '/reject', headers=admin, json={'reviewed_by': 'forged', 'reason': 'No evidence'}).status_code == 200
    record = json.loads((api.REJECTED_DIR / f'{rid}.json').read_text())
    assert record['reviewed_by'] != 'forged'
    assert record['reject_reason'] == 'No evidence'
    assert client.get('/api/approved').json() == []


def test_submission_cannot_assert_approved_consent(client):
    admin = auth(client, 'admin')
    response = client.post('/api/submit', headers=admin, json={'title': 'Fiction', 'text': 'Test',
                           'attribution': META})
    rid = response.json()['id']
    assert api._all_pending_records()[rid]['attribution'] == {}
    assert client.post(f'/api/items/{rid}/approve', headers=admin,
                       json={'reviewed_by': 'x', 'access': 'public'}).status_code == 422
