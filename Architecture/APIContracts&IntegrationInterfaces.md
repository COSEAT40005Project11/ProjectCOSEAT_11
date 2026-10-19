# API Contracts and Integration Interfaces


## 1. Overview

This document outlines the proposed API contracts and integration interfaces for the Traditional Knowledge Repository.

The purpose is to establish how the system's main components are intended to communicate, exchange information and coordinate operations relating to knowledge submission, processing, review, storage and retrieval.

The document builds upon the existing high-level system architecture and component responsibilities documentation, providing further clarification of the communication pathways between the web frontend, backend API, data ingestion pipeline, AI processing and retrieval, speech-to-text processing, quarantine and human-in-the-loop (HITL) review, access control and relational database.

The current project repository includes an initial FastAPI backend with endpoints supporting knowledge submission, review operations, retrieval and basic status information. These existing interfaces provide a starting point for defining the wider system integration requirements.

The contracts and interfaces described in this document distinguish between existing functionality and proposed or outstanding integration requirements. They are intended to support subsequent development, implementation and validation, and may be refined as project requirements and stakeholder expectations are further clarified.



## 2. API and Integration Overview


### 2.1 Backend API as the Central Communication Layer

The backend API serves as the primary communication and coordination layer between the system's user-facing interface and its supporting processing, review and storage components.

Its intended integration responsibilities include:

- Receiving requests from the web frontend and returning appropriate responses.
- Coordinating knowledge submission and retrieval operations.
- Supporting the quarantine and human review workflow.
- Communicating with ingestion and AI-assisted processing components.
- Interacting with the relational database for structured data operations.
- Applying appropriate request validation and access restrictions.
- Supporting consistent information exchange between system components.

The existing backend implementation uses FastAPI and provides HTTP endpoints for several baseline repository operations.

Further development is required to establish complete integration with the proposed relational database, implement appropriate server-side authorisation and validate communication between the wider system components.


### 2.2 Communication and Data Exchange

Communication between the web frontend and backend API is primarily based on HTTP requests and responses.

The existing API uses JSON-compatible request and response structures to exchange information relating to knowledge submissions, review decisions, approved records and retrieval operations.

The main proposed communication pathways include:

- Web Frontend ↔ Backend API: User requests, knowledge submissions, review operations and returned information.
- Backend API ↔ Access Control: Permission checks and authorisation decisions.
- Backend API ↔ Relational Database: Structured data storage, retrieval and management operations.
- Backend API → Data Ingestion Pipeline: Coordination of incoming knowledge processing.
- Data Ingestion Pipeline → Speech-to-Text Processing: Audio transcription requests and draft transcript generation.
- Data Ingestion Pipeline → AI Processing and Retrieval: Content preparation and AI-assisted processing.
- Data Ingestion Pipeline → Quarantine & HITL Review: Submission of processed information for human verification.
- AI Processing and Retrieval → Quarantine & HITL Review: AI-generated suggestions requiring human assessment.
- Quarantine & HITL Review → Backend API: Review decisions and outcomes.
- Backend API ↔ AI Processing and Retrieval: Retrieval requests and corresponding results.

These pathways describe the intended component relationships rather than confirming that every connection has been fully implemented.

The current implementation primarily coordinates selected frontend, review and retrieval operations through the backend API, while the ingestion workflow produces records for the review queue.

Further integration work is required to establish consistent communication and data exchange across all proposed components.


### 2.3 Current Implementation and Proposed Interfaces

The project currently contains an initial backend implementation in `API/app.py`, which defines endpoints for retrieving pending and approved knowledge items, submitting information, approving or rejecting records, retrieving basic review statistics and performing source-grounded knowledge retrieval.

The existing implementation uses JSON files within the `AIOutput/` directory to maintain pending, approved and rejected records.

This file-based storage provides an initial mechanism for supporting the baseline review workflow but does not represent the completed relational database integration proposed in the system architecture.

The intended relational database will provide a more structured foundation for managing knowledge items, users, tags, cultural protocols and their associated relationships.

The current API also does not yet establish comprehensive authentication, server-side role-based authorisation or culturally appropriate access enforcement. These remain important requirements for subsequent implementation and validation.

Accordingly, the following sections document the existing API endpoints and identify the additional contracts and integration requirements needed to support the proposed repository architecture.



## 3. Existing Backend API Contracts

The current backend implementation defines several HTTP endpoints for supporting knowledge submission, review, retrieval and basic repository status operations.

These endpoints are implemented using FastAPI in `API/app.py` and provide an initial communication interface between the web frontend and the supporting repository functionality.

The following subsections document the existing endpoint definitions, expected inputs, returned information and relevant implementation considerations.


### 3.1 Retrieve Pending Knowledge Items

**Endpoint:** `GET /api/pending`

**Purpose:**

Retrieves knowledge items awaiting human review.

**Request:**

- No request body or parameters are required.

**Response:**

Returns a JSON array containing pending knowledge records.

Each record may include:

- `id`: Unique identifier for the knowledge item.
- `title`: Title of the submitted knowledge.
- `summary`: Summary associated with the submission.
- `original_text`: Original content available for reviewer verification.
- `status`: Current review status.
- `confidence`: Relevance score used for review prioritisation.
- `access`: Assigned access classification.
- `source`: Source or citation information.
- `source_meta`: Additional source metadata.

Additional fields may describe the source file, content chunk and summarisation method.

**Implementation Considerations:**

The endpoint reads pending records from the existing file-based storage and excludes items that have already been approved or rejected.

Pending items are sorted by their relevance scores, with higher-scoring records appearing first.

The `confidence` field currently represents a relevance signal rather than a validated measure of AI-generated answer confidence.


### 3.2 Retrieve Approved Knowledge Items

**Endpoint:** `GET /api/approved`

**Purpose:**

Retrieves knowledge items that have been approved through the review workflow.

**Request:**

- No request body or parameters are required.

**Response:**

Returns a JSON array of approved knowledge records using the same general item structure as the pending knowledge endpoint.

**Implementation Considerations:**

The current implementation retrieves records from the approved JSON storage directory.

Further integration with the proposed relational database and cultural access control mechanisms is required to support structured storage and appropriate restrictions on knowledge retrieval.


### 3.3 Retrieve Repository Review Statistics

**Endpoint:** `GET /api/stats`

**Purpose:**

Provides basic information about the current state of the repository's review workflow.

**Request:**

- No request body or parameters are required.

**Response:**

Returns a JSON object containing:

- `pending`: Number of knowledge items awaiting review.
- `approved`: Number of approved knowledge records.
- `rejected`: Number of rejected knowledge records.

**Implementation Considerations:**

The current implementation calculates these values using the pending, approved and rejected JSON storage directories.

These statistics provide a basic overview of review activity rather than comprehensive repository analytics.


### 3.4 Submit a Knowledge Item

**Endpoint:** `POST /api/submit`

**Purpose:**

Allows a knowledge item to be submitted for subsequent human review.

**Request Body:**

- `title` (string, required): Title of the knowledge item.
- `text` (string, required): Submitted knowledge content.
- `access` (string, optional): Requested access classification, defaulting to `community`.
- `source` (string, optional): Source description, defaulting to `Manual submission`.

**Response:**

Returns a JSON object containing:

- `ok`: Indicates that the submission operation completed.
- `id`: Unique identifier generated for the submitted item.

**Implementation Considerations:**

The current implementation creates a new pending record with a generated identifier and stores it within the file-based review queue.

The submitted content is not automatically approved for general repository access.

Further validation, consent handling and culturally appropriate submission controls remain necessary for the proposed system.


### 3.5 Approve a Knowledge Item

**Endpoint:** `POST /api/items/{item_id}/approve`

**Purpose:**

Records the approval of a pending knowledge item following human review.

**Path Parameter:**

- `item_id`: Unique identifier of the knowledge item being reviewed.

**Request Body:**

- `reviewed_by` (string, required): Identifier or name of the reviewer.
- `access` (string, optional): Access classification, defaulting to `community`.
- `summary` (string or null, optional): Revised summary provided by the reviewer.
- `original_text` (string or null, optional): Revised source content provided by the reviewer.

**Response:**

Returns a JSON object containing:

- `ok`: Indicates whether the operation completed.
- `status`: Updated status, set to `approved`.
- `id`: Identifier of the reviewed item.

**Implementation Considerations:**

The current implementation retrieves the pending record, applies any supplied content revisions and writes the approved record to the corresponding JSON storage directory.

The approval record also includes reviewer information and a review timestamp.

If the requested item cannot be found in the pending records, the endpoint returns an HTTP 404 error.

The existing implementation records reviewer information but does not independently verify that the reviewer has appropriate authority to approve the knowledge item.


### 3.6 Reject a Knowledge Item

**Endpoint:** `POST /api/items/{item_id}/reject`

**Purpose:**

Records the rejection of a pending knowledge item following human review.

**Path Parameter:**

- `item_id`: Unique identifier of the knowledge item being reviewed.

**Request Body:**

- `reviewed_by` (string, required): Identifier or name of the reviewer.
- `reason` (string or null, optional): Explanation for the rejection decision.

**Response:**

Returns a JSON object containing:

- `ok`: Indicates whether the operation completed.
- `status`: Updated status, set to `rejected`.
- `id`: Identifier of the reviewed item.

**Implementation Considerations:**

The current implementation records the rejected item, reviewer information, review timestamp and optional rejection reason in the rejected JSON storage directory.

If the requested item cannot be found in the pending records, the endpoint returns an HTTP 404 error.

As with the approval operation, appropriate reviewer authentication and authorisation remain outstanding integration requirements.


### 3.7 Retrieve Knowledge-Based Answers

**Endpoint:** `GET /api/ask`

**Purpose:**

Supports question-based retrieval of information from approved knowledge records.

**Query Parameters:**

- `q` (string, required): Question submitted by the user.
- `access` (string, optional): Requested access classification, defaulting to `community`.

**Response:**

Returns the result produced by the existing retrieval component.

The exact response structure is determined by the implementation in `Models/retrieval.py`.

**Implementation Considerations:**

The current backend delegates retrieval operations to the existing retrieval module.

The intended behaviour is to return source-grounded information from approved knowledge records rather than generate unsupported answers.

The current request interface accepts an access classification supplied by the caller. This does not constitute secure user authorisation.

Further development is required to ensure that access restrictions are enforced using authenticated user permissions and applicable cultural protocols.


### 3.8 Check Backend API Health

**Endpoint:** `GET /health`

**Purpose:**

Provides a basic mechanism for checking whether the backend API is responding.

**Request:**

- No request body or parameters are required.

**Response:**

Returns a JSON object containing:

- `status`: Set to `ok`.

**Implementation Considerations:**

This endpoint provides a basic application health response.

It does not independently verify the availability or operational state of the database, ingestion pipeline, AI processing components or other supporting services.


### 3.9 Existing API Limitations

Although the current API provides a useful baseline for repository operations, several aspects require further development before the proposed system can be considered fully integrated.

The main limitations include:

- File-based JSON storage rather than integration with the proposed relational database.
- Absence of comprehensive server-side authentication and role-based authorisation.
- Incomplete enforcement of community-defined cultural access restrictions.
- Limited validation of submitted access classifications and reviewer authority.
- Outstanding integration and validation across the wider ingestion, processing and review components.
- Need for more consistent error handling and verification of component interactions.

These limitations provide a starting point for defining the additional integration contracts and implementation requirements in the following sections.



## 4. Proposed Component Integration Interfaces

This section defines the proposed integration interfaces between the main components of the Traditional Knowledge Repository.

These interfaces build upon the communication pathways established in the high-level system architecture and describe the intended information exchanges, responsibilities and integration considerations.

The interfaces represent an initial design specification rather than a complete implementation. Their detailed request structures, service boundaries and technical requirements may be refined as the corresponding components are developed and integrated.


### 4.1 Web Frontend and Backend API

The web frontend communicates with the backend API to support user interactions with the repository.

**Proposed Interface:**

- Communication through HTTP requests and JSON responses.
- Submission of knowledge content for processing and review.
- Retrieval of approved knowledge records.
- Submission of review decisions through authorised interfaces.
- Retrieval of basic repository and review status information.

**Integration Considerations:**

The frontend should communicate with the repository through defined backend endpoints rather than directly accessing underlying storage.

The backend must validate incoming requests and enforce appropriate access permissions independently of the frontend interface.

Existing FastAPI endpoints provide a baseline for several of these interactions, although further authentication, authorisation and integration testing are required.


### 4.2 Backend API and Relational Database

The backend API is intended to coordinate structured data operations involving the relational database.

**Proposed Interface:**

- Creation and retrieval of knowledge item records.
- Storage and management of user information.
- Management of tags and cultural protocol associations.
- Updating consent, review and access classification information.
- Retrieval of records according to applicable access restrictions.

**Data Exchange:**

The database integration will use the proposed relational schema containing the following six tables:

- `Knowledge_Items`
- `Users`
- `Tags`
- `Cultural_Protocols`
- `Knowledge_Item_Tags`
- `Knowledge_Item_Protocols`

The backend will interact with these tables through database operations rather than exposing direct database access to the frontend.

**Integration Considerations:**

The proposed database will replace or supplement the existing file-based JSON storage mechanism as the repository progresses towards structured data management.

Database operations should maintain referential integrity, validate submitted information and support consistent handling of knowledge item relationships.

Further implementation and validation are required to establish this interface.


### 4.3 Backend API and Data Ingestion Pipeline

The data ingestion pipeline is responsible for preparing incoming knowledge content for subsequent processing and review.

**Proposed Interface:**

- Initiation or coordination of knowledge submission and ingestion operations.
- Transfer of submitted content and associated metadata.
- Communication of processing status and outcomes.
- Routing of prepared information towards AI-assisted processing and human review.

**Data Exchange:**

Information exchanged may include:

- Submission identifiers.
- Knowledge titles and content.
- Source or provenance information.
- Content type and relevant metadata.
- Processing status and error information.

**Integration Considerations:**

The ingestion workflow should preserve the original source information and maintain traceability between submitted content and processed records.

Newly ingested information should not become generally accessible without the required review and approval processes.

The existing ingestion implementation provides a baseline for preparing records for review, while further integration with the backend and database remains necessary.


### 4.4 Data Ingestion Pipeline and Speech-to-Text Processing

The speech-to-text component supports the conversion of authorised audio material into draft textual content.

**Proposed Interface:**

- Transfer of audio material or references to authorised audio files.
- Initiation of transcription processing.
- Return of generated draft transcripts.
- Communication of transcription status and processing errors.

**Data Exchange:**

Information exchanged may include:

- Audio file references.
- Source metadata.
- Generated transcript text.
- Processing status.
- Transcription-related metadata where available.

**Integration Considerations:**

The existing Whisper-based functionality provides an initial foundation for audio transcription.

Generated transcripts must be treated as draft material requiring appropriate human verification before acceptance into the repository.

The ingestion workflow should preserve the relationship between the original audio source and the generated transcript.

Further integration is required to establish a consistent transcription and review workflow.


### 4.5 Data Ingestion Pipeline and AI Processing

The ingestion pipeline may communicate with AI processing components to support the preparation and organisation of submitted knowledge.

**Proposed Interface:**

- Transfer of prepared text and associated metadata.
- Submission of content for AI-assisted analysis.
- Return of suggested summaries, classifications or descriptive tags.
- Communication of processing outcomes and relevant confidence information.

**Data Exchange:**

Information exchanged may include:

- Knowledge item identifiers.
- Prepared content.
- Source references.
- Suggested summaries and tags.
- Processing status and associated metadata.

**Integration Considerations:**

AI-generated information should be treated as preliminary suggestions rather than authoritative knowledge classifications.

The processing workflow should retain source information and distinguish original content from AI-generated interpretations.

Any confidence scores used for AI-assisted classification must have clearly defined meanings and should not independently determine whether culturally significant knowledge is approved or accessible.


### 4.6 AI Processing and Retrieval and Backend API

The AI processing and retrieval component supports the identification and retrieval of relevant knowledge through backend-coordinated operations.

**Proposed Interface:**

- Submission of user queries through the backend API.
- Transfer of relevant retrieval parameters.
- Retrieval of approved and appropriately accessible knowledge.
- Return of source-grounded results to the backend.

**Data Exchange:**

Information exchanged may include:

- User queries.
- Access-related parameters.
- Relevant knowledge records.
- Source references.
- Retrieved information and response metadata.

**Integration Considerations:**

The existing `/api/ask` endpoint provides a baseline interface for knowledge retrieval.

The backend must ensure that retrieval operations respect authenticated user permissions and applicable cultural access restrictions.

AI-assisted retrieval should use authorised knowledge sources and avoid presenting generated interpretations as verified cultural knowledge.

Further integration and testing are required to establish consistent retrieval behaviour across the proposed repository.


### 4.7 Processing Components and Quarantine & HITL Review

The quarantine and human-in-the-loop review component provides a controlled mechanism for assessing submitted and processed knowledge before approval.

**Proposed Interface:**

- Receipt of submitted knowledge records from the ingestion pipeline.
- Receipt of AI-generated suggestions requiring human assessment.
- Receipt of draft transcripts requiring verification.
- Presentation of relevant source information to authorised reviewers.
- Recording of review decisions and any permitted modifications.

**Data Exchange:**

Information exchanged may include:

- Knowledge item identifiers.
- Original submitted content.
- Generated summaries, tags or transcripts.
- Source and provenance information.
- Review status.
- Reviewer decisions and supporting explanations.

**Integration Considerations:**

The review workflow should maintain a clear distinction between original submissions, automated processing outputs and human-approved information.

Appropriate community representatives must retain authority over decisions concerning culturally significant knowledge.

Reviewers should be able to assess relevant source material before approving, modifying or rejecting records, subject to their permissions.

The existing pending, approval and rejection API operations provide a baseline for review-related functionality, although comprehensive reviewer authorisation and workflow integration remain outstanding.


### 4.8 Quarantine & HITL Review and Backend API

The quarantine and human review component communicates review decisions and outcomes through the backend API.

**Proposed Interface:**

- Retrieval of pending knowledge records for authorised review.
- Submission of approval or rejection decisions.
- Submission of permitted content modifications.
- Updating knowledge item review status.
- Communication of review outcomes for subsequent storage or processing.

**Data Exchange:**

Information exchanged may include:

- Knowledge item identifiers.
- Reviewer identifiers.
- Review decisions.
- Revised content or access classifications.
- Rejection reasons.
- Review timestamps.

**Integration Considerations:**

The existing approval and rejection endpoints provide an initial mechanism for recording review decisions.

Further development must ensure that review actions are restricted to appropriately authorised users.

Review outcomes should be recorded consistently and linked to the corresponding knowledge records to support traceability and accountability.

The backend should coordinate subsequent storage and retrieval operations according to the approved review outcomes and applicable cultural protocols.


### 4.9 Backend API and Access Control

The access control component is intended to determine whether users are permitted to perform particular repository operations or access specific knowledge records.

**Proposed Interface:**

- Submission of permission checks by the backend API.
- Evaluation of user roles and access classifications.
- Consideration of applicable cultural protocols and consent requirements.
- Return of access decisions to the backend.
- Enforcement of access decisions before protected operations proceed.

**Data Exchange:**

Information exchanged may include:

- Authenticated user identifiers.
- User roles and permissions.
- Requested operations.
- Knowledge item identifiers.
- Applicable access classifications and cultural protocols.
- Authorisation decisions.

**Integration Considerations:**

Access control must be enforced by the backend rather than relying on frontend restrictions or user-supplied access classifications.

The proposed access control mechanism should support community-defined restrictions and distinguish between different levels of authorisation.

Access decisions should be evaluated before sensitive information is returned, modified, approved or otherwise processed.

The current backend does not yet provide comprehensive server-side authorisation, making this an important requirement for subsequent development and integration.



## 5. General Integration Considerations

The proposed API contracts and integration interfaces establish an initial foundation for communication between the main components of the Traditional Knowledge Repository.

As development progresses, several considerations will need to be addressed to support consistent, secure and reliable integration.


### 5.1 Data Exchange and Consistency

Communication between the frontend and backend should use consistent request and response structures, with JSON serving as the primary format for API data exchange.

The backend should validate incoming information before processing or storing it, ensuring that required fields, identifiers and data formats are handled appropriately.

Integration with the relational database should maintain consistency between knowledge records, users, tags and cultural protocols, while preserving the relationships defined in the proposed database schema.


### 5.2 Error Handling and Processing Status

API operations should provide meaningful responses indicating whether requests have succeeded or failed.

Errors involving invalid submissions, missing records, processing failures or restricted access should be handled consistently and communicated through appropriate response structures and HTTP status codes.

Processing workflows should also maintain clear status information so that submitted knowledge can be tracked through ingestion, automated processing and human review.


### 5.3 Security and Cultural Access Restrictions

The repository must account for authentication, authorisation, consent requirements and cultural access restrictions when handling traditional knowledge.

The backend should enforce access decisions before allowing protected operations or returning restricted information.

Cultural protocols and community-defined permissions should be considered throughout the ingestion, review, storage and retrieval workflows.

AI-generated outputs must not independently override human review decisions or community authority over culturally significant knowledge.


### 5.4 Component Integration and Testing

As individual components are implemented, their integration interfaces should be tested to verify that information is exchanged correctly and that the intended workflows operate as expected.

Integration testing should consider:

- Correct handling of API requests and responses.
- Consistent data exchange between components.
- Validation of submitted information.
- Appropriate handling of processing errors.
- Correct enforcement of review and access restrictions.
- Preservation of knowledge item relationships and processing status.

These activities will help verify that the implemented components align with the proposed architecture and support the intended repository functionality.



## 6. Outstanding Integration Processes

The API contracts and integration interfaces documented here provide an initial technical specification for the Traditional Knowledge Repository.

Although the existing backend establishes a baseline for several repository operations, further development is required to implement and validate the complete proposed architecture.

The main areas requiring further work include:

- Finalising detailed API request and response structures where necessary.
- Implementing and integrating the proposed relational database schema.
- Establishing consistent communication between ingestion, AI processing and speech-to-text components.
- Completing the quarantine and human-in-the-loop review workflow.
- Implementing comprehensive backend authentication and access control.
- Integrating cultural protocol and consent requirements into relevant operations.
- Testing component interactions and validating the overall system behaviour.

These activities may be addressed progressively as the corresponding components are developed and integrated.

The proposed interfaces may also be refined through implementation findings, team collaboration and stakeholder feedback.



## 7. Summary

This document defines the initial API contracts and proposed integration interfaces for the Traditional Knowledge Repository.

It identifies the existing backend API operations, describes the intended communication between the repository's major components and outlines the main considerations for subsequent development and integration.

Together with the high-level system architecture, component responsibilities documentation and proposed database schema, this document contributes to a common technical foundation for the project.

The documented interfaces provide a reference for future implementation, testing and refinement as the repository progresses towards a more integrated and functional system.

