# Database Schema Design

## 1. Overview

This document defines the relational database schema design for the Traditional Knowledge Repository. The design translates the identified database requirements into entities, attributes and relationships that support repository content, cultural protocols, access conditions, tagging, provenance and human review.

The schema provides a straightforward initial structure for the current prototype requirements. Entities, attributes and relationships may be extended or revised as repository components and workflow requirements are further defined. 

The initial (Sprint 1) schema contained six tables. The latest (Sprint 2) revision extends this structure to eight tables, introducing `knowledge_sources` for source provenance and `review_history` for recording individual human review decisions. The `knowledge_items` table has also been extended to accommodate fields relevant to the existing JSON-based ingestion and review workflow.

The proposed schema is defined in `database_schema.sql`, targeting MySQL Community Server 8.4. The SQL has been prepared for an empty development database but has not yet been executed or validated. The schema does not itself perform JSON migration, enforce application-level access authorisation or establish cultural consent.



## 2. Schema Entities

### 2.1 Knowledge Items

The `knowledge_items` table represents the central content stored and managed by the repository. The revised structure retains the original knowledge item attributes while introducing fields to support source references, ingested content, AI-assisted summaries and processing metadata.

| Attribute | Key | Description |
|---|---|---|
| `item_id` | Primary Key | Unique knowledge item identifier, stored as `CHAR(36)` to preserve existing backend UUIDs |
| `title` | | Title of the knowledge item |
| `content` | | Legacy content field retained for compatibility with the initial design |
| `original_text` | | Original text associated with an ingested knowledge item |
| `summary` | | Summary associated with the knowledge item |
| `content_type` | | Content type, defaulting to `text` |
| `source` | | Legacy source or provenance display value |
| `source_id` | Foreign Key | Optional reference to `knowledge_sources.source_id` |
| `source_file` | | Original source filename or file reference |
| `chunk_index` | | Index of a content segment within its source |
| `cultural_category` | | Cultural classification associated with the item |
| `access_classification` | | Access category, defaulting to `restricted` |
| `consent_status` | | Consent status, defaulting to `unknown` |
| `review_status` | | Current review state, defaulting to `pending` |
| `summary_method` | | Method used to produce the summary, where recorded |
| `relevance_score` | | Optional relevance score between 0 and 1 |
| `created_by` | Foreign Key | Optional reference to `users.user_id` |
| `ingested_at` | | Timestamp associated with ingestion, where recorded |
| `created_at` | | Database record creation timestamp |
| `updated_at` | | Most recent modification timestamp |

The `source_id` and `created_by` foreign keys are nullable. If a referenced source or user is deleted, the corresponding foreign key is set to `NULL`.

The `access_classification`, `consent_status`, `review_status` and `relevance_score` fields are subject to SQL check constraints, documented in the schema implementation.

The `content` and `source` fields are retained as legacy design fields, while `original_text` and `source_id` provide more specific representations for ingested content and source provenance.

**Relationship considerations:** A knowledge item may reference one source and one creating user. It may also be associated with multiple tags, cultural protocols and review history records.


### 2.2 Users

The `users` table represents individuals who interact with the repository and provides the basic user information required to support repository responsibilities and future access-control functionality.

| Attribute | Key | Description |
|---|---|---|
| `user_id` | Primary Key | Unique identifier for the user |
| `display_name` | | Name used to identify the user within the repository |
| `role` | | Repository role associated with the user |
| `account_status` | | Current status of the user account |
| `created_at` | | Creation information for the user record |
| `updated_at` | | Most recent modification information |


### 2.3 Tags

The `tags` table represents descriptive labels used to organise, classify and support the retrieval of knowledge items.

| Attribute | Key | Description |
|---|---|---|
| `tag_id` | Primary Key | Unique identifier for the tag |
| `tag_name` | | Name of the tag |
| `tag_description` | | Brief description of the tag |
| `tag_source` | | Indicates the origin of the tag, such as manual or AI-assisted |
| `review_status` | | Current review or approval state of the tag |
| `created_at` | | Creation information for the tag record |


### 2.4 Knowledge Item Tags

The `knowledge_item_tags` table connects knowledge items with their associated tags. It supports the many-to-many relationship between the two entities without duplicating tag information.

| Attribute | Key | Description |
|---|---|---|
| `item_id` | Primary Key, Foreign Key | References `knowledge_items.item_id` |
| `tag_id` | Primary Key, Foreign Key | References `tags.tag_id` |

The combination of `item_id` and `tag_id` forms a composite primary key, preventing the same tag from being associated with the same knowledge item more than once.

**Initial relationship:** One knowledge item may have multiple tags, and one tag may be associated with multiple knowledge items.


### 2.5 Cultural Protocols

The `cultural_protocols` table represents cultural handling and access conditions that may apply to repository knowledge. The database stores the relevant protocol information but does not independently determine culturally appropriate access or handling decisions.

| Attribute | Key | Description |
|---|---|---|
| `protocol_id` | Primary Key | Unique identifier for the cultural protocol |
| `protocol_name` | | Name used to identify the protocol |
| `protocol_description` | | Description of the protocol or guidance |
| `access_condition` | | Access condition associated with the protocol |
| `created_at` | | Creation information for the protocol record |
| `updated_at` | | Most recent modification information |


### 2.6 Knowledge Item Protocols

The `knowledge_item_protocols` table connects knowledge items with applicable cultural protocols. It supports the many-to-many relationship between knowledge items and protocols while keeping protocol information separately maintained.

| Attribute | Key | Description |
|---|---|---|
| `item_id` | Primary Key, Foreign Key | References `knowledge_items.item_id` |
| `protocol_id` | Primary Key, Foreign Key | References `cultural_protocols.protocol_id` |

The combination of `item_id` and `protocol_id` forms a composite primary key, preventing the same protocol from being associated with the same knowledge item more than once.

**Initial relationship:** One knowledge item may be associated with multiple cultural protocols, and one cultural protocol may apply to multiple knowledge items.


### 2.7 Knowledge Sources

The `knowledge_sources` table stores source provenance and reference information separately from individual knowledge items. This allows multiple knowledge items or content segments to reference the same source without duplicating its metadata.

| Attribute | Key | Description |
|---|---|---|
| `source_id` | Primary Key | Auto-incrementing source identifier |
| `source_title` | | Title of the source, where available |
| `source_author` | | Author or attributed creator, where available |
| `publication_year` | | Publication year or date-related text |
| `source_url` | | URL associated with the source |
| `source_note` | | Additional source or provenance notes |
| `source_file` | | Source filename or file reference |
| `source_metadata` | | Additional structured metadata stored as JSON |
| `created_at` | | Source record creation timestamp |

The `source_id` primary key uses `BIGINT UNSIGNED AUTO_INCREMENT`. Other source metadata fields are optional in the current SQL design.

**Relationship:** One knowledge source may be referenced by multiple knowledge items through `knowledge_items.source_id`.

Source provenance information supports traceability but does not independently establish cultural consent or permission to access knowledge.


### 2.8 Review History

The `review_history` table records individual human review decisions associated with knowledge items. It maintains a history of decisions separately from the current `review_status` stored in `knowledge_items`.

| Attribute | Key | Description |
|---|---|---|
| `review_id` | Primary Key | Auto-incrementing review record identifier |
| `item_id` | Foreign Key | References `knowledge_items.item_id` |
| `reviewer_name` | | Recorded name of the reviewer |
| `decision` | | Review decision, restricted to `approved` or `rejected` |
| `reason` | | Optional explanation of the decision |
| `reviewed_at` | | Timestamp of the review decision |
| `reviewed_summary` | | Summary associated with the review, where recorded |
| `reviewed_original_text` | | Original text associated with the review, where recorded |

The `review_id` primary key uses `BIGINT UNSIGNED AUTO_INCREMENT`. The `item_id`, `reviewer_name`, `decision` and `reviewed_at` fields are required.

The `decision` field is constrained to `approved` or `rejected`. The `item_id` foreign key uses `ON DELETE RESTRICT`, preventing deletion of a knowledge item while related review history records exist.

The `reviewer_name` field stores reviewer information as text and is not currently linked to the `users` table through a foreign key.

**Relationship:** One knowledge item may have multiple review history records. Each review history record references one knowledge item.

The presence of a review decision does not independently establish reviewer authorisation or cultural permission.



## 3. Entity Relationships

The initial database schema uses relationships between the core entities to avoid unnecessary duplication and maintain consistent references between repository information.


### 3.1 User to Knowledge Items

One user may create multiple knowledge items, while each knowledge item references one creating user.

**Relationship:** One-to-Many

`users.user_id` → `knowledge_items.created_by`


### 3.2 Knowledge Items to Tags

A knowledge item may have multiple tags, and a tag may be associated with multiple knowledge items. This many-to-many relationship is represented through the `knowledge_item_tags` junction table.

**Relationship:** Many-to-Many

`knowledge_items.item_id` → `knowledge_item_tags.item_id`

`tags.tag_id` → `knowledge_item_tags.tag_id`


### 3.3 Knowledge Items to Cultural Protocols

A knowledge item may be associated with multiple cultural protocols, and a cultural protocol may apply to multiple knowledge items. This many-to-many relationship is represented through the `knowledge_item_protocols` junction table.

**Relationship:** Many-to-Many

`knowledge_items.item_id` → `knowledge_item_protocols.item_id`

`cultural_protocols.protocol_id` → `knowledge_item_protocols.protocol_id`



## 4. Initial Design Scope

The initial schema intentionally focuses on the core information and relationships required by the current prototype. Review, consent and source information are represented using straightforward attributes within the existing entities where appropriate.

Additional entities or attributes may be introduced if later repository components require more detailed review histories, consent management, provenance records or access-control information. This allows the schema to evolve without introducing unnecessary complexity during the initial prototype stage.
