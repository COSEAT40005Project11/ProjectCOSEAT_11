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



## 4. Data Migration and Backend Integration


### 4.1 Migration Process

The proposed migration process consists of the following stages:

1. Preserve a backup of the existing JSON data before making changes.
2. Read and validate pending, approved and rejected records according to their existing JSON structures.
3. Match multiple occurrences of the same knowledge item using the existing item identifier.
4. Identify conflicting records or review outcomes for investigation rather than silently overwriting information.
5. Map validated knowledge content, source metadata and current review status into the corresponding relational tables.
6. Preserve supported review decisions and reviewer-confirmed tags through their related tables.
7. Record migration outcomes and verify that repeated execution does not create duplicate knowledge items or review events.
8. Compare migrated records and API outputs with the original data before changing the application's storage behaviour.

The existing pending files may contain arrays of records, while approved and rejected files may contain individual record objects. These formats must be handled appropriately during parsing.

Where the same item appears in multiple storage locations, the migration should create one current knowledge item record and preserve any supported review history. Unresolved conflicting outcomes should be reported rather than arbitrarily selected.


### 4.2 Backend Data Access

The backend API provides the interface through which repository components perform supported database operations.

The proposed integration responsibilities include:

- Validating incoming record data before insertion or update.
- Translating existing API request fields into database columns and relationships.
- Retrieving knowledge items according to their review status and authorised access conditions.
- Recording review decisions and associated changes consistently.
- Managing tag and protocol associations through the corresponding junction tables.
- Preserving expected API response structures where existing frontend functionality depends on them.

The retrieval workflow must also use the database-backed source of approved records when the application transitions away from JSON storage. Updating API endpoints alone would not complete that transition.


### 4.3 Database Consistency

Database operations should use transactions where multiple related changes must succeed together. Primary keys, foreign keys and constraints should be used to protect record integrity.

Subsequent structural changes should be managed through explicit schema migrations. Re-running an initial `CREATE TABLE IF NOT EXISTS` script does not update existing table definitions or constraints.



## 5. Validation Considerations

The database mapping and integration should be validated before being treated as operational.

Validation activities should cover:

- Correct creation of the proposed tables, keys, constraints and relationships.
- Preservation of existing knowledge item identifiers and source metadata.
- Correct handling of pending, needs-review, approved and rejected states.
- Accurate storage of review decisions without fabricated history.
- Prevention of duplicate records during repeated migrations.
- Correct storage of reviewer-confirmed tags and cultural protocol associations.
- Appropriate handling of missing consent and restricted access information.
- Consistency of relevant backend API responses before and after integration.

Initial testing should use synthetic records rather than real culturally sensitive material. Successful schema creation, migration and API integration should be established through executed tests and recorded results.



## 6. Synopsis

This document outlines the proposed mapping between the Traditional Knowledge Repository's existing data structures and its relational database schema.

It describes the handling of knowledge items, source attribution, review history, user roles, cultural access information and descriptive tags, alongside the main considerations for migration and backend integration.

Together with the database requirements, schema definition, ER diagram and API integration documentation, this mapping provides a reference for implementing and validating consistent data storage across the repository's components.
