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

