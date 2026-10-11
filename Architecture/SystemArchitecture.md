# High-Level System Architecture


## 1. Overview

This document defines the proposed high-level system architecture for the Traditional Knowledge Repository.

The system aims to support the collection, processing, review, storage and retrieval of traditional knowledge while respecting community authority, consent requirements and cultural access restrictions.

The architecture consists of several interconnected components responsible for user interaction, backend coordination, data ingestion, AI-assisted processing, human review, structured data storage and access control.

The design provides an initial technical foundation for the development and integration of these components. It may be refined as project requirements are clarified through team collaboration and stakeholder feedback.



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

- Importing information from approved and credible documents or sources.
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


### 2.9 Simulated Offline and Kiosk Interface

The proposed simulated offline or kiosk-style interface supports accessibility in environments with limited connectivity.

Its intended responsibilities include:

- Providing accessible navigation for repository users.
- Supporting interaction under low-bandwidth conditions.
- Exploring pictographic and voice-assisted interfaces.
- Supporting the retrieval of appropriately approved information where offline functionality is available.
- Demonstrating selected kiosk-style capabilities without requiring physical kiosk hardware.

Offline functionality must preserve the same cultural access restrictions and consent requirements as the connected system.



## 3. Proposed High-Level System Workflow

The intended system workflow consists of the following stages:

1. Knowledge is submitted through approved documents, manual entry or authorised audio recordings.
2. The ingestion pipeline receives and prepares the submitted information.
3. Speech-to-text or other AI-assisted components may generate draft transcripts, summaries or suggested classifications.
4. Incoming and AI-generated information enters the quarantine and human-review workflow.
5. An appropriately authorised reviewer checks the information for accuracy, consent and applicable cultural requirements.
6. Information may be approved, corrected or rejected according to the review outcome.
7. Approved information becomes eligible for repository storage and retrieval, subject to applicable access restrictions.
8. The backend coordinates requests and applies the required validation and access-control rules.
9. The frontend presents information that the requesting user is authorised to access.

This workflow represents the proposed architectural flow between the system's major components.

