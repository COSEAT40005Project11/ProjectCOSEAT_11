# High-Level System Architecture


## 1. Overview

This document defines the proposed high-level system architecture for the Traditional Knowledge Repository.

The system aims to support the collection, processing, review, storage and retrieval of traditional knowledge while respecting community authority, consent requirements and cultural access restrictions.

The architecture consists of several interconnected components responsible for user interaction, backend coordination, data ingestion, AI-assisted processing, human review, structured data storage and access control.

The design provides an initial technical foundation for the development and integration of these components. It may be modified as project requirements are clarified throughout the development along with stakeholder feedback.



## 2. Main System Components

### 2.1 Web Frontend

The web frontend provides the user-facing interface for interacting with the Traditional Knowledge Repository.

Its intended responsibilities include:

- Allowing users to browse and search approved knowledge items.
- Supporting the submission of information for processing and review.
- Providing interfaces for authorised review activities.
- Displaying knowledge according to applicable access restrictions.
- Supporting accessible interaction through simple navigation and interface design.

The frontend communicates with the backend API to request information and perform supported operations.


### 2.2 Backend API

The backend API provides the communication and coordination layer between the frontend, data storage and processing components.

Its intended responsibilities include:

- Receiving and processing requests from the frontend.
- Coordinating knowledge submission and retrieval operations.
- Supporting review and approval workflows.
- Communicating with the database and ingestion components.
- Applying application-level validation and access restrictions.
- Returning appropriate responses to requesting components.

The backend acts as a central interface through which the system's major components interact.


### 2.3 Data Ingestion Pipeline

The data ingestion pipeline is responsible for receiving and preparing incoming knowledge for processing and review.

The project proposes two primary ingestion methods:

- Importing information from authorised and credible documents or sources.
- Processing authorised audio recordings through speech-to-text transcription.

Its intended responsibilities include:

- Receiving submitted knowledge and source materials.
- Preparing information for further processing.
- Coordinating with speech-to-text and other AI-assisted components.
- Forwarding processed information into the quarantine and review workflow.
- Preserving relevant source information for verification and traceability.

Information obtained through ingestion must undergo appropriate validation before becoming approved repository content.


### 2.4 Speech-to-Text Processing

The speech-to-text component uses automatic speech recognition technology, such as Whisper, to convert authorised audio recordings into draft text.

Its intended responsibilities include:

- Receiving audio input through the ingestion workflow.
- Generating draft transcriptions.
- Providing transcription output for subsequent verification.
- Supporting future improvements in transcription accuracy.

Generated transcripts must undergo appropriate human review before being approved for repository use.


### 2.5 AI Processing and Retrieval

AI-assisted processing components support the preparation, organisation and retrieval of knowledge.

Their intended responsibilities may include:

- Generating suggested summaries or classifications.
- Assisting with descriptive tagging of knowledge items.
- Supporting the identification and retrieval of relevant information.
- Providing AI-generated outputs for human verification where required.
- Supporting future confidence-based processing and review decisions.

AI-generated content must not be treated as automatically verified or approved. The retrieval process must respect applicable review, consent and access-control requirements.


### 2.6 Quarantine and Human-in-the-Loop Review

The quarantine and human-in-the-loop (HITL) review component is intended to prevent unverified information from entering the approved repository.

Its intended responsibilities include:

- Holding incoming information pending review.
- Allowing authorised reviewers to inspect information against its original source.
- Supporting approval, correction or rejection decisions.
- Preventing unapproved information from becoming available through normal repository retrieval.
- Supporting the traceability of review decisions.

The review process must consider information accuracy, consent requirements and applicable cultural protocols. Only appropriately approved information may proceed towards normal repository storage and retrieval.


### 2.7 Relational Database

The relational database provides structured storage for the repository's core information.

The initial database design identifies six tables:

- `users`
- `knowledge_items`
- `tags`
- `knowledge_item_tags`
- `cultural_protocols`
- `knowledge_item_protocols`

These tables represent knowledge records, user information, descriptive classifications and applicable cultural protocols.

The database design also includes fields for source information, consent status, review status and access classification. The database supports relationships between knowledge items, their creators, associated tags and applicable cultural protocols. The database provides the underlying data structure, while the backend and related components are responsible for implementing the necessary application logic.


### 2.8 Access Control

The access-control component regulates which knowledge items may be accessed by different users.

Its intended responsibilities include:

- Evaluating applicable access classifications and cultural protocols.
- Restricting information according to authorised permissions.
- Considering review and consent status before information is made available.
- Supporting changes to access permissions and consent decisions.
- Preventing unauthorised access to restricted knowledge.

The proposed access categories include public, community-only, restricted and sacred. These categories must be applied according to appropriate community governance and approved system requirements. Access-control decisions must be enforced through the backend rather than relying solely on frontend visibility restrictions.



## 3. Proposed High-Level System Workflow

The intended system workflow consists of the following stages:

1. Knowledge is submitted through credible documents, manual entries or authorised audio recordings.
2. The ingestion pipeline receives and prepares the submitted information.
3. Speech-to-text or other AI-assisted components may generate draft transcripts, summaries or suggested classifications.
4. Incoming and AI-generated information enters the quarantine and human-review workflow.
5. An appropriately authorised reviewer checks the information for accuracy, consent and applicable cultural requirements.
6. Information may be approved, corrected or rejected according to the review outcome.
7. Approved information becomes eligible for repository storage and retrieval, subject to applicable access restrictions.
8. The backend coordinates requests and applies the required validation and access-control rules.
9. The frontend presents information that the requesting user is authorised to access.

This workflow represents the proposed architectural flow between the system's major components.



## 4. Component Communication and Integration

The proposed architecture requires communication between several major components.


### 4.1 Frontend and Backend

The frontend communicates with the backend API to submit requests and receive information. The backend processes these requests and applies the appropriate application rules. The frontend should not independently determine whether restricted information may be accessed.


### 4.2 Backend and Ingestion Components

The backend coordinates incoming knowledge submissions with the ingestion and processing components. The ingestion pipeline prepares information for subsequent verification and storage.


### 4.3 Ingestion and AI Processing

The ingestion pipeline interacts with speech-to-text and other AI-assisted components where automated processing is required. These components produce draft outputs that may require additional validation before approval.


### 4.4 Ingestion and Human Review

Information produced through ingestion and AI processing must pass through the appropriate review workflow before being treated as approved repository content. The review process supports verification against original sources and consideration of consent and cultural requirements.


### 4.5 Backend and Database

The backend interacts with the relational database to create, retrieve and update structured repository records. The database stores the information required by repository operations, while the backend coordinates application behaviour.


### 4.6 Access Control and Retrieval

The backend and retrieval components apply appropriate access restrictions when returning repository information. Access decisions must account for approved cultural protocols, consent requirements, review status and user permissions. Restricted or unapproved information must not be exposed through unauthorised retrieval operations.



## 5. Architectural Design Considerations

The following considerations guide the initial system architecture:

- **Modularity:** Components should have clearly defined responsibilities to support independent development and integration.
- **Data Integrity:** Repository information should be stored and managed in a structured and consistent manner.
- **Human Validation:** AI-generated information must undergo appropriate review before approval.
- **Cultural Safety:** Knowledge must be handled according to approved cultural protocols and community authority.
- **Access Control:** Repository content must only be made available to appropriately authorised users.
- **Consent Management:** The system must support the appropriate handling of consent and future changes to consent decisions.
- **Traceability:** Important processing, review and access decisions should be auditable.
- **Maintainability:** The architecture should support changes as requirements and implementation decisions evolve.
- **Accessibility:** The system should consider users with limited connectivity, literacy or access to personal devices.
- **Integration:** Components should communicate through clearly defined interfaces to support reliable system operation.



## 6. Architectural Integration Considerations

The system architecture identifies several important dependencies between components.


### 6.1 Database and Backend Integration

The backend requires an appropriate interface for interacting with the relational database. Database operations must support the storage and retrieval of knowledge items and their associated information.


### 6.2 Ingestion and Review Integration

The ingestion pipeline must communicate with the quarantine and review workflow. This ensures that incoming and AI-generated information cannot bypass the required verification process.


### 6.3 Review and Repository Storage

The review workflow must distinguish between pending, approved and rejected information. Only appropriately approved information should become eligible for normal repository retrieval, subject to applicable consent and access restrictions.


### 6.4 Access Control and Cultural Governance

Access-control functionality must operate consistently with the repository's cultural protocols, consent requirements and user permissions. The architecture must support restrictions determined through appropriate community governance rather than assuming that all knowledge can be shared publicly.


### 6.5 Component Interfaces

The frontend, backend, ingestion pipeline, AI-processing components and database require clearly defined communication interfaces. Detailed API contracts, request formats, response structures and error-handling arrangements will be documented separately as part of the system integration design.



## 7. Potential Future Extensions

A simulated offline or kiosk-style interface may be considered in later project stages to support accessible repository interaction in environments with limited connectivity.

Potential capabilities include accessible navigation, pictographic or voice-assisted interaction, and retrieval of appropriately approved information under limited-connectivity conditions.

If introduced, the interface may integrate with existing repository services to provide an alternative method of accessing information.

Any future implementation would need to preserve cultural access restrictions, consent requirements and community authority over repository information, including responding appropriately to changes in permissions or consent.



## 8. Summary

The proposed high-level architecture establishes an initial technical foundation for the Traditional Knowledge Repository by identifying its major components and their intended interactions. 

The design separates user interaction, backend coordination, data ingestion, AI-assisted processing, human review, structured storage and access control into distinct areas of responsibility. 

This approach supports incremental development and integration while keeping cultural governance, human validation and responsible handling of traditional knowledge central to the system.

The architecture may be refined as the system requirements and features are clarified through implementation, integration, testing, and feedback.
