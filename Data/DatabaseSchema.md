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

This revised database schema defines relationships across eight tables using primary keys, foreign keys and junction tables. These relationships support referential integrity, source provenance, descriptive tagging, cultural protocol associations and historical review records.

### 3.1 Users to Knowledge Items

One user may be recorded as the creator of multiple knowledge items. Each knowledge item may reference one creating user, although this reference is optional.

**Relationship:** One-to-Many

`users.user_id` → `knowledge_items.created_by`

The `created_by` foreign key is nullable and uses `ON DELETE SET NULL`, allowing the knowledge item to remain when the referenced user is deleted.


### 3.2 Knowledge Sources to Knowledge Items

One knowledge source may be associated with multiple knowledge items or content segments. Each knowledge item may reference one source record.

**Relationship:** One-to-Many

`knowledge_sources.source_id` → `knowledge_items.source_id`

The `source_id` foreign key is nullable and uses `ON DELETE SET NULL`. The knowledge item can therefore remain if its associated source record is deleted, although its structured source reference will be cleared.


### 3.3 Knowledge Items to Tags

A knowledge item may have multiple tags, and a tag may be associated with multiple knowledge items. This many-to-many relationship is represented through the `knowledge_item_tags` junction table.

**Relationship:** Many-to-Many

`knowledge_items.item_id` → `knowledge_item_tags.item_id`

`tags.tag_id` → `knowledge_item_tags.tag_id`

The junction table uses the composite primary key (`item_id`, `tag_id`) to prevent duplicate associations.

Both foreign keys use `ON DELETE CASCADE`, so deleting a referenced knowledge item or tag removes the corresponding junction records.


### 3.4 Knowledge Items to Cultural Protocols

A knowledge item may be associated with multiple cultural protocols, and a cultural protocol may apply to multiple knowledge items. This many-to-many relationship is represented through the `knowledge_item_protocols` junction table.

**Relationship:** Many-to-Many

`knowledge_items.item_id` → `knowledge_item_protocols.item_id`

`cultural_protocols.protocol_id` → `knowledge_item_protocols.protocol_id`

The junction table uses the composite primary key (`item_id`, `protocol_id`) to prevent duplicate associations.

Both foreign keys use `ON DELETE CASCADE`, so deleting a referenced knowledge item or cultural protocol removes the corresponding junction records. These database rules do not replace the need for culturally appropriate governance of protocol changes.


### 3.5 Knowledge Items to Review History

One knowledge item may have multiple historical review records. Each review history record must reference one existing knowledge item.

**Relationship:** One-to-Many

`knowledge_items.item_id` → `review_history.item_id`

The `item_id` foreign key is required and uses `ON DELETE RESTRICT`. This prevents deletion of a knowledge item while associated review history records remain.

The `reviewer_name` attribute is stored as text rather than as a foreign key to `users`. Reviewer identity and authorisation must therefore be addressed outside this relationship.


### 3.6 Referential Integrity and Validation Constraints

The proposed SQL schema includes constraints intended to support data consistency and valid relationships.

**Primary and foreign keys:**
- Primary keys uniquely identify records in each table.
- Foreign keys connect knowledge items to users and knowledge sources.
- Junction-table foreign keys connect knowledge items to tags and cultural protocols.
- Review history records reference existing knowledge items.

**Knowledge item check constraints:**
- `access_classification`: `public`, `community`, `restricted`, `sacred`
- `consent_status`: `unknown`, `pending`, `granted`, `denied`, `withdrawn`
- `review_status`: `pending`, `needs_review`, `approved`, `rejected`
- `relevance_score`: `NULL` or a value between `0` and `1`, inclusive

**Review history check constraint:**
- `decision`: `approved` or `rejected`

**Additional integrity provisions:**
- `tags.tag_name` must be unique.
- Junction tables use composite primary keys to prevent duplicate associations.
- The SQL defines indexes on knowledge item review/access fields, source references and review history item/timestamp fields.

These constraints describe the intended SQL design. Their behaviour has not yet been confirmed through database execution and validation.

Database constraints alone do not enforce cultural consent, reviewer authorisation or application-level access permissions.



## 4. Initial Design Scope

The initial schema intentionally focuses on the core information and relationships required by the current prototype. Review, consent and source information are represented using straightforward attributes within the existing entities where appropriate.

Additional entities or attributes may be introduced if later repository components require more detailed review histories, consent management, provenance records or access-control information. This allows the schema to evolve without introducing unnecessary complexity during the initial prototype stage.



## 5. Revised Design Scope and Implementation Status

This section extends the initial design scope described in Section 4, documenting the subsequent schema revisions and their current implementation status.

The Sprint 1 database design established six initial tables representing knowledge items, users, tags, cultural protocols and their associated junction tables.

The Sprint 2 revision extends this design to eight tables by introducing `knowledge_sources` and `review_history`. It also expands `knowledge_items` to accommodate fields used by the existing JSON-based ingestion and review workflow.


### 5.1 Current Schema Deliverables

The database design is represented by the following artefacts:

- `DatabaseRequirements.md` documents the repository's database requirements.
- `DatabaseSchema.md` describes the relational entities, attributes, relationships and constraints.
- `database_schema.sql` contains the proposed MySQL 8.4 database creation statements.
- `DatabaseMapping.md` describes the proposed mapping between existing JSON-based repository records and the relational schema.
- The accompanying versions of the entity-relationship diagrams illustrate the database structure and its evolution.

The SQL script is intended for an empty development database. It defines the proposed table structure but does not migrate existing JSON records.


### 5.2 Implementation and Validation Boundaries

The following activities remain separate from the preparation of the schema documentation and SQL definitions:

- Executing the SQL script against a MySQL development database.
- Verifying table creation, primary keys, foreign keys and check constraints.
- Testing database operations using synthetic or otherwise authorised non-sensitive data.
- Validating relationships and deletion behaviour.
- Implementing and testing JSON-to-database migration.


### 5.3 Proposed Future Database Activities

- Constructing the database in a local environment to test overall composition.
- Creating and validating the actual database using the proposed SQL schema.
- Integrating the database with the existing backend and application workflows.
- Developing a data access layer to support database operations and migration from the existing JSON-based records.
- Refining database schema or structure as necessary based on changes to other components of the repository system. 
- Migrating appropriately authorised real data and testing database functionality, relationships and constraints.


### 5.4 Cultural Governance and Future Development

The relational schema provides fields and relationships to support consent tracking, access classification, cultural protocol associations, provenance and human review.

However, the existence of these fields does not independently establish culturally appropriate access, consent or reviewer authority. Such requirements also depend on application-level controls, approved processes and appropriate stakeholder governance.

Further refinements may be necessary following SQL validation, integration testing and stakeholder feedback. Any subsequent schema changes should be reflected in the SQL script, database documentation and revised entity-relationship diagram.
