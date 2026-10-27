# Sprint 2: review, consent and attribution mapping

This is a design mapping and evidence guide, not a claim of compliance or community approval. The client-meeting presentation states that only public, non-sensitive material should be used before ethics approval. The AIATSIS Code addresses Aboriginal and Torres Strait Islander research in Australia; confirm with the client how it should inform work involving Bangladeshi communities.

## Implementation and evidence

- New manual submissions enter the existing pending JSON queue; ingestion output remains pending until human review.
- Custodian/admin permissions (`consent:manage`) control the attribution update endpoint. The API stores community, credit, language, consent status, consent and authority references, permitted use and allowed access. These are assertions; the reviewer must verify evidence separately.
- Approval requires granted consent and populated governance fields, including authority and consent references. Allowed access must match the approved access level. Reviewer-confirmed tags are preserved.
- Approval and rejection use the authenticated token subject as reviewer ID. Rejection requires a reason; a second decision returns conflict. A pending record remains as a source record and its decision is saved separately.
- Public approved responses and retrieval include credit fields but omit consent and authority references. Tag suggestions require reviewer permission and sufficient clearance.
- `python -m pytest -q` exercises consent, clearance, decision recording, tag preservation and the existing tagging tests.

## CARE mapping

| Principle | Supporting feature | Remaining work |
| --- | --- | --- |
| Collective Benefit | Attribution and permitted-use fields record the intended use and community credit. | Communities determine benefit and reciprocity; a field cannot establish them. |
| Authority to Control | Consent manager records authority and allowed access before human approval. | Real community-scoped permissions, validation of authority, and withdrawal after publication. |
| Responsibility | Reviewer identity and timestamps support accountability. | Long-term stewardship, full version history and audit policy. |
| Ethics | Pending quarantine and human review reduce premature publication. | Assess harms with communities; avoid real community data without permission. |

## AIATSIS Code mapping

| Principle | Supporting feature | Remaining work |
| --- | --- | --- |
| Indigenous self-determination | Records consent and scope before approval. | Community-led decisions and verified authority cannot be supplied by code alone. |
| Indigenous leadership | Human review and consent-manager permission. | Community must decide who is authorised; demo roles are not evidence of community leadership. |
| Impact and value | Permitted use and attribution fields. | Establish impacts, benefit and reciprocity with the relevant community. |
| Sustainability and accountability | Decision snapshots and reviewer/time metadata. | Durable storage, retention, backups, withdrawal and complete event history. |

Sources: https://ardc.edu.au/resource/the-care-principles/ and https://aiatsis.gov.au/research/ethical-research/research-ethics-framework

## Integration limits

This change uses the team's existing JWT authentication and file-based JSON storage. The frontend login is not yet connected to the backend, and the current frontend has no attribution editor, so review using `/docs` with synthetic content. The shared lock is only safe inside one server process; it is not a database transaction and does not protect multiple workers. Decision reversal and withdrawal after publication require a separate, authorised workflow. Public caching may retain previously distributed records. Metadata edits only retain the last editor, not complete history. The user's JWT subject identifies the reviewer; it is not a verified community affiliation or readable display name. Existing approved legacy records have not been re-reviewed for consent. Database migration and community-specific access are separate team tasks. Do not claim these features make the repository safe for real sensitive knowledge.
