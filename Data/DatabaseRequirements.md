# Core Database Requirements

## 1. Purpose

The database will provide the core data layer for the Traditional Knowledge Repository by storing the information required to manage repository content, users, cultural protocols, access conditions and associated metadata. The database requirements are defined to support the repository's planned ingestion, review, access-control and retrieval functionality while maintaining traceability, human oversight and culturally appropriate handling of knowledge.



## 2. Core Data Entities

### 2.1 Knowledge Item

A knowledge item represents an individual piece of content managed by the repository. It is the central repository entity and must retain sufficient information to identify the content, describe its origin and classification, determine its current review state, and support appropriate access decisions. 

Required information may include:

- Unique item identifier
- Title and content or content reference
- Content type
- Source or provenance information
- Cultural category
- Access classification
- Consent status
- Review or quarantine status
- Creation and update information


### 2.2 User

A user represents an individual who interacts with the repository. User information must support identification, role-based responsibilities and appropriate access to repository content and functionality.

Required information may include:

- Unique user identifier
- Name or display name
- User role
- Access level or permissions
- Account status
- Creation and update information


### 2.3 Tag

A tag represents a descriptive label associated with repository content. Tags support the organisation, classification and retrieval of knowledge items and may later include tags proposed through AI-assisted functionality and confirmed through human review.

Required information may include:

- Unique tag identifier
- Tag name
- Tag description
- Tag source or origin
- Review or approval status
- Creation information


### 2.4 Cultural Protocol

A cultural protocol represents a rule, condition or guidance associated with the culturally appropriate handling and access of repository knowledge. Protocol information must support the repository's access-control and human-review processes without allowing automated functionality to override culturally governed decisions.

Required information may include:

- Unique protocol identifier
- Protocol name
- Protocol description
- Applicable cultural category
- Access conditions or restrictions
- Approval or review information
- Creation and update information


### 2.5 Knowledge Source

A knowledge source represents the origin or reference material associated with one or more repository knowledge items. Source information should be maintained separately where appropriate to support provenance, attribution and traceability without unnecessarily duplicating the same source details across multiple knowledge records.

Required information may include:

- Unique source identifier
- Source title and author, where available
- Publication year or other relevant date information
- Source URL or reference
- Source notes and original file information
- Additional structured source metadata
- Creation information

A single source may be associated with multiple knowledge items or processed content segments. Source records must not be interpreted as evidence of consent or authorisation on their own.


### 2.6 Review History

A review history record represents an individual human review decision associated with a knowledge item. Review history should be maintained separately from the item's current review status to support accountability, traceability and preservation of previous decisions.

Required information may include:

- Unique review record identifier
- Associated knowledge item identifier
- Reviewer name or recorded reviewer information
- Review decision
- Reason or explanation, where available
- Review timestamp
- Reviewed summary or original text, where available

A knowledge item may have multiple review history records. Recording a review decision does not independently establish cultural authority or permission to disclose restricted knowledge.



## 3. Supporting Information Requirements

In addition to the core entities, the repository must retain supporting information required to manage knowledge appropriately throughout its lifecycle. This information should support traceability, cultural governance, human review and subsequent repository functionality.

Supporting information requirements include:

- Source and provenance information, including references to source records and original source files where available.
- Original knowledge text and AI-assisted summaries, where applicable.
- Source metadata and processing information, including content segment or chunk references where relevant.
- Consent status associated with knowledge items.
- Cultural categories and access classifications.
- Quarantine and current review status.
- Human review decisions, reviewer information, review timestamps and associated reasons.
- Historical review records maintained separately from the current review status.
- Descriptive tags and their review status.
- Cultural protocols and their associations with knowledge items.
- Creation, modification and ingestion timestamps where applicable.

The database should distinguish a knowledge item's current review state from its historical review decisions. Source attribution and review history should remain traceable as records progress through the repository workflow.

The presence of source information, a review decision or an approved status must not independently be treated as proof of cultural consent or authorisation to access restricted knowledge.



## 4. Relationship Requirements

The database must support relationships between the identified entities without unnecessarily duplicating data. The proposed relational structure includes the following relationships:

- **Knowledge Source to Knowledge Item (one-to-many):** A knowledge source may be associated with multiple knowledge items. Each knowledge item may reference one source record, where applicable.

- **User to Knowledge Item (one-to-many):** A user may be recorded as the creator of multiple knowledge items. Each knowledge item may reference one creator, where available.

- **Knowledge Item to Tag (many-to-many):** A knowledge item may have multiple tags, and a tag may be associated with multiple knowledge items. This relationship is represented through the `knowledge_item_tags` junction table.

- **Knowledge Item to Cultural Protocol (many-to-many):** A knowledge item may be associated with multiple cultural protocols, and a protocol may apply to multiple knowledge items. This relationship is represented through the `knowledge_item_protocols` junction table.

- **Knowledge Item to Review History (one-to-many):** A knowledge item may have multiple historical review records. Each review history record belongs to one knowledge item.

The relationships should be represented using primary keys, foreign keys and junction tables where appropriate. Referential integrity should be maintained to prevent invalid associations between records.

The proposed schema records reviewer information in `review_history` using a reviewer name rather than a foreign key to the `users` table. Consequently, the database relationship structure does not independently verify reviewer identity or authorisation.

The detailed attributes, keys, constraints and relationship definitions are documented in `DatabaseSchema.md` and the accompanying `database_schema.sql` file.



## 5. Design Considerations

The database requirements are guided by the following considerations:

- **Cultural governance:** Cultural protocols, consent requirements and access restrictions must be respected throughout repository processes. Database fields and relationships support these requirements, but application-level authorisation and community governance processes remain necessary.

- **Human oversight:** Human review must remain part of the approval workflow for repository knowledge. Historical review decisions should be retained to support accountability and traceability.

- **Source provenance:** Knowledge items should retain sufficient information to identify their origins, including associated source records, source files and relevant metadata where available.

- **Data integrity:** Primary keys, foreign keys, uniqueness constraints and applicable validation constraints should support consistency between related database records.

- **Existing backend compatibility:** The relational schema should account for relevant fields from the existing JSON-based backend, including knowledge item identifiers, original text, summaries, processing metadata and review information.

- **Development and testing:** Synthetic or non-sensitive test data should be used during development and validation. Genuine culturally sensitive knowledge must not be imported without appropriate authorisation.

- **Extensibility:** The data structure should support subsequent repository functionality and integration without introducing unnecessary complexity.

- **Incremental implementation:** The SQL schema provides a proposed relational database structure for the repository. Database execution, validation, migration and backend integration are separate implementation activities and should only be reported as completed once verified.

The requirements and associated schema may be refined as the prototype develops and further stakeholder requirements are clarified.
