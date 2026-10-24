# Database Mapping and Translation


## 1. Outline

This document defines the proposed mapping of repository data into the relational database for the Traditional Knowledge Repository.

Its purpose is to establish a consistent approach to storing knowledge records, source information, review decisions, user details, descriptive tags and cultural access information. It also describes how existing data structures can be translated into the proposed database schema while preserving record identity and relevant relationships.

The mapping provides a technical reference for subsequent database implementation, data migration and backend integration. The described processes are proposed arrangements and may be refined during implementation and testing.



## 2. Data Storage and Mapping Approach

The repository's existing data handling uses JSON records for knowledge processing and review. The relational database is intended to provide structured storage for these records and their associated information.

The database mapping should:

- Preserve existing knowledge item identifiers across storage formats.
- Separate knowledge content from source attribution and review history.
- Maintain relationships between knowledge items, tags and cultural protocols.
- Distinguish current review status from recorded review decisions.
- Preserve access classifications and consent information without inferring authorisation.
- Support consistent retrieval and updating of records through the backend API.


### 2.1 Knowledge Record Mapping

| Existing data field | Proposed database destination | Purpose |
| --- | --- | --- |
| `id` | `knowledge_items.item_id` | Preserves the existing knowledge item identifier. |
| `source.title` | `knowledge_items.title`, `knowledge_sources.source_title` | Records the item title and source title. |
| `original_text` | `knowledge_items.original_text` | Stores the original or reviewed source text. |
| `summary` | `knowledge_items.summary` | Stores the associated summary. |
| `status` | `knowledge_items.review_status` | Identifies the current processing or review state. |
| `access` | `knowledge_items.access_classification` | Records the assigned access classification. |
| `summary_method` | `knowledge_items.summary_method` | Identifies the summarisation method where available. |
| `relevance_score` | `knowledge_items.relevance_score` | Stores a valid processing relevance score where available. |
| `ingested_at` | `knowledge_items.ingested_at` | Preserves the ingestion timestamp. |
| `source_file` | `knowledge_items.source_file`, `knowledge_sources.source_file` | Records the associated input file or submission source. |
| `chunk_index` | `knowledge_items.chunk_index` | Preserves the position of a processed content segment. |

Existing item identifiers should remain unchanged during migration to maintain continuity with backend operations and references. Missing optional values should be represented appropriately rather than replaced with invented information.


### 2.2 Source and Attribution Mapping

Source information is represented through `knowledge_sources`, with individual knowledge items referencing their associated source through `source_id`.

The source mapping includes:

- `source.title` to `source_title`.
- `source.author` to `source_author`.
- `source.year` to `publication_year`.
- `source.url` to `source_url`.
- `source.note` to `source_note`.
- Additional structured source information to `source_metadata`.

A source may be associated with multiple knowledge items or processed content segments. Source identity should be determined using sufficiently reliable identifying information rather than a title alone, which may not uniquely identify a document.

The mapping supports the preservation of available attribution and provenance details. It does not, by itself, establish that all cultural attribution or ethical requirements have been satisfied.


### 2.3 Review and Approval Mapping

The current status of a knowledge item is stored in `knowledge_items.review_status`. The proposed schema accommodates `pending`, `needs_review`, `approved` and `rejected` states.

Individual review decisions are represented in `review_history` using the knowledge item identifier, reviewer name, decision, optional reason and review timestamp. Where available, reviewed content snapshots can also be retained.

The following fields are mapped where supported by the source record:

| Existing data field | Proposed database destination |
| --- | --- |
| `reviewed_by` | `review_history.reviewer_name` |
| `reviewed_at` | `review_history.reviewed_at` |
| `reject_reason` | `review_history.reason` |
| Reviewed `summary` | `review_history.reviewed_summary` |
| Reviewed `original_text` | `review_history.reviewed_original_text` |

Review events should only be created from available evidence of an actual decision. Historical decisions that are no longer present in the source data cannot be reconstructed reliably.



## 3. Related Data and Access Information


### 3.1 User and Role Information

The `users` table represents repository user records through a stable `user_id`, display name, role and account status. These fields provide a basis for associating users with application-level operations.

Roles such as `viewer`, `reviewer`, `custodian` and `admin` may be represented by `users.role`. The database stores the role value; the backend is responsible for validating authenticated identities and enforcing the permissions associated with each role.

A display name must not be treated as proof of an authenticated identity. Existing free-text reviewer names may be preserved in review history without assuming they correspond to verified user accounts.

Credentials and signing secrets must not be stored in repository source files. The proposed database schema does not currently define an authentication credential store.


### 3.2 Cultural Access and Consent

The `knowledge_items.access_classification` field records an item's access level, using `public`, `community`, `restricted` or `sacred`. The `consent_status` field separately represents consent information using `unknown`, `pending`, `granted`, `denied` or `withdrawn`.

Cultural handling requirements can be associated with knowledge items through `cultural_protocols` and `knowledge_item_protocols`.

Database classifications provide information for access-control decisions but do not independently grant permission to view, publish or modify culturally sensitive material. Access must be checked through the backend against applicable roles, consent conditions and cultural protocols. Unknown or missing consent must not be interpreted as approval.


### 3.3 Tag Mapping

Descriptive tags are stored in `tags` and associated with knowledge items through `knowledge_item_tags`.

Reviewer-confirmed tags may be mapped to these tables after normalisation and duplicate checking. AI-generated tag suggestions should remain distinguishable from confirmed associations and should not automatically be treated as approved metadata.

The current relational structure supports confirmed tag associations. Persistent storage of suggestion confidence, supporting evidence or suggestion history would require a separately defined data structure if introduced.
