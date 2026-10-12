# Responsibilities of System Components


## 1. Outline

This document defines the proposed responsibilities and boundaries of the main components within the Traditional Knowledge Repository. 

The purpose is to establish a clear separation of responsibilities between user interaction, backend coordination, knowledge ingestion, AI-assisted processing, human review, data storage and access control. 

These responsibilities provide a foundation for component integration and the subsequent definition of API contracts and communication interfaces. 

The responsibilities may be refined as project requirements are clarified through team collaboration and stakeholder feedback.



## 2. Component Responsibilities


### 2.1 Web Frontend

The web frontend is responsible for providing the user-facing interface through which users interact with the repository.

Primary responsibilities:

- Presenting interfaces for browsing and searching approved knowledge.
- Supporting the submission of information and source materials.
- Providing appropriate interfaces for authorised review activities.
- Displaying information returned by the backend.
- Supporting accessible navigation and interaction.

Responsibility boundaries:

- Does not independently determine whether a user is authorised to access restricted information.
- Does not directly modify repository database records.
- Communicates with backend services to perform supported operations.


### 2.2 Backend API

The backend API is responsible for coordinating communication and operations between the frontend and other system components.

Primary responsibilities:

- Receiving and processing requests from the frontend.
- Coordinating knowledge submission, review and retrieval operations.
- Validating requests and applying application-level rules.
- Communicating with ingestion, review and data-storage components.
- Coordinating access-control checks before returning information.
- Providing appropriate responses and error information.

Responsibility boundaries:

- Does not independently determine cultural authority or consent decisions.
- Does not treat AI-generated information as automatically approved.
- Delegates specialised processing to the appropriate components.


### 2.3 Data Ingestion Pipeline

The data ingestion pipeline is responsible for receiving and preparing incoming knowledge for subsequent processing and review.

Primary responsibilities:

- Receiving approved source documents and authorised submissions.
- Preparing submitted content for processing.
- Coordinating document-based and audio-based ingestion.
- Passing appropriate inputs to AI-processing components.
- Preserving source information needed for verification.
- Forwarding processed information to the quarantine and review workflow.

Responsibility boundaries:

- Does not independently approve or publish knowledge.
- Does not bypass required human-review processes.
- Does not determine cultural access permissions.


### 2.4 Speech-to-Text Processing

The speech-to-text component is responsible for converting authorised audio recordings into draft text.

Primary responsibilities:

- Receiving audio inputs from the ingestion workflow.
- Processing audio using automatic speech recognition technology.
- Producing draft transcripts for subsequent verification.
- Returning transcription outputs to the ingestion or review workflow.

Responsibility boundaries:

- Does not independently verify the cultural or factual accuracy of transcripts.
- Does not approve transcripts for publication.
- Does not determine access permissions for transcribed material.


### 2.5 AI Processing and Retrieval

AI-assisted processing components are responsible for supporting the organisation, classification and retrieval of knowledge.

Primary responsibilities:

- Producing suggested summaries or descriptive classifications.
- Supporting AI-assisted tagging of knowledge items.
- Assisting with the identification of relevant repository information.
- Supporting retrieval operations involving approved knowledge.
- Providing generated outputs for verification where required.

Responsibility boundaries:

- Does not automatically approve or publish generated information.
- Does not independently determine cultural protocols or consent.
- Must operate within the review and access restrictions enforced by the wider system.


### 2.6 Quarantine and Human-in-the-Loop Review

The quarantine and human-in-the-loop (HITL) review component is responsible for managing the verification of incoming knowledge before approval.

Primary responsibilities:

- Maintaining the review status of incoming information.
- Holding unreviewed information in quarantine.
- Supporting authorised reviewers in inspecting submitted material.
- Supporting approval, correction and rejection decisions.
- Recording relevant review outcomes for traceability.
- Preventing unapproved information from entering normal repository retrieval.

Responsibility boundaries:

- Does not automatically approve AI-generated information.
- Does not replace the authority of appropriately designated cultural custodians or reviewers.
- Requires coordination with backend validation, consent management and access-control processes.


### 2.7 Relational Database

The relational database is responsible for providing structured storage of repository information.

Primary responsibilities:

- Storing knowledge items and their associated metadata.
- Storing user records and relevant account information.
- Maintaining descriptive tags and cultural protocol records.
- Representing relationships between knowledge items, tags and protocols.
- Supporting data integrity through appropriate database constraints.
- Providing structured data access for authorised backend operations.

Responsibility boundaries:

- Does not independently determine whether knowledge is culturally appropriate for publication.
- Does not replace backend validation or access-control logic.
- Does not independently perform ingestion, AI processing or human review.


### 2.8 Access Control

The access-control component is responsible for evaluating and enforcing repository access restrictions.

Primary responsibilities:

- Evaluating user permissions and access classifications.
- Considering applicable cultural protocols and consent requirements.
- Supporting restrictions on public, community-only, restricted and sacred information.
- Preventing unauthorised retrieval of protected knowledge.
- Supporting changes to permissions and consent-related restrictions.
- Providing access decisions for backend operations.

Responsibility boundaries:

- Does not independently establish cultural governance rules.
- Does not replace the human-review process.
- Must apply rules approved through appropriate community governance and project requirements.


### 2.9 Simulated Offline and Kiosk Interface

The simulated offline or kiosk-style interface is responsible for supporting accessible repository interaction in environments with limited connectivity.

Primary responsibilities:

- Providing accessible navigation and interaction.
- Supporting pictographic or voice-assisted interface features.
- Supporting approved repository browsing under limited-connectivity conditions.
- Demonstrating selected offline-capable functionality.

Responsibility boundaries:

- Does not bypass access-control or consent requirements.
- Must not expose restricted information through unauthorised offline storage or retrieval.
- Relies on appropriately governed repository information and services.
