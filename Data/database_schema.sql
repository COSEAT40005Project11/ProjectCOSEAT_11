-- Intended platform for SQL block(s) below is MySQL Community Server version 8.4. 
-- Development only. No live cultural knowledge should be imported without authorisation.
-- Apply to an EMPTY development database. This file does not migrate existing JSON.
-- Execution: mysql -u <your_user> -p < database_schema.sql



CREATE DATABASE IF NOT EXISTS traditional_knowledge_repository
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE traditional_knowledge_repository;



CREATE TABLE IF NOT EXISTS users (
  user_id CHAR(36) PRIMARY KEY,
  display_name VARCHAR(255) NOT NULL,
  role VARCHAR(60) NOT NULL DEFAULT 'contributor',
  account_status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS knowledge_sources (
  source_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  source_title VARCHAR(500),
  source_author VARCHAR(255),
  publication_year VARCHAR(30),
  source_url TEXT,
  source_note TEXT,
  source_file VARCHAR(500),
  source_metadata JSON,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS knowledge_items (
  item_id CHAR(36) PRIMARY KEY, -- preserve existing backend UUIDs
  title VARCHAR(500) NOT NULL,
  content LONGTEXT, -- legacy design field; prefer original_text for ingested content
  original_text LONGTEXT,
  summary LONGTEXT,
  content_type VARCHAR(80) NOT NULL DEFAULT 'text',
  source TEXT, -- legacy provenance display value
  source_id BIGINT UNSIGNED NULL,
  source_file VARCHAR(500),
  chunk_index INT UNSIGNED,
  cultural_category VARCHAR(120),
  access_classification VARCHAR(30) NOT NULL DEFAULT 'restricted',
  consent_status VARCHAR(30) NOT NULL DEFAULT 'unknown',
  review_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  summary_method VARCHAR(80),
  relevance_score DECIMAL(7,6),
  created_by CHAR(36) NULL,
  ingested_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

  CONSTRAINT fk_item_creator
    FOREIGN KEY (created_by) REFERENCES users(user_id)
    ON DELETE SET NULL,

  CONSTRAINT fk_item_source
    FOREIGN KEY (source_id) REFERENCES knowledge_sources(source_id)
    ON DELETE SET NULL,

  CONSTRAINT chk_item_access
    CHECK (access_classification IN (
      'public', 'community', 'restricted', 'sacred'
    )),

  CONSTRAINT chk_item_review
    CHECK (review_status IN (
      'pending', 'needs_review', 'approved', 'rejected'
    )),

  CONSTRAINT chk_item_consent
    CHECK (consent_status IN (
      'unknown', 'pending', 'granted', 'denied', 'withdrawn'
    )),

  CONSTRAINT chk_item_relevance
    CHECK (
      relevance_score IS NULL
      OR (relevance_score >= 0 AND relevance_score <= 1)
    ),

  INDEX idx_item_review_access (review_status, access_classification),
  INDEX idx_item_source (source_id)
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS tags (
  tag_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tag_name VARCHAR(255) NOT NULL UNIQUE,
  tag_description TEXT,
  tag_source VARCHAR(40) NOT NULL DEFAULT 'manual',
  review_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS knowledge_item_tags (
  item_id CHAR(36) NOT NULL,
  tag_id BIGINT UNSIGNED NOT NULL,

  PRIMARY KEY (item_id, tag_id),

  CONSTRAINT fk_kit_item
    FOREIGN KEY (item_id) REFERENCES knowledge_items(item_id)
    ON DELETE CASCADE,

  CONSTRAINT fk_kit_tag
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS cultural_protocols (
  protocol_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  protocol_name VARCHAR(255) NOT NULL,
  protocol_description TEXT,
  access_condition TEXT,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS knowledge_item_protocols (
  item_id CHAR(36) NOT NULL,
  protocol_id BIGINT UNSIGNED NOT NULL,

  PRIMARY KEY (item_id, protocol_id),

  CONSTRAINT fk_kip_item
    FOREIGN KEY (item_id) REFERENCES knowledge_items(item_id)
    ON DELETE CASCADE,

  CONSTRAINT fk_kip_protocol
    FOREIGN KEY (protocol_id) REFERENCES cultural_protocols(protocol_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS review_history (
  review_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  item_id CHAR(36) NOT NULL,
  reviewer_name VARCHAR(255) NOT NULL,
  decision VARCHAR(30) NOT NULL,
  reason TEXT,
  reviewed_at DATETIME(6) NOT NULL,
  reviewed_summary LONGTEXT,
  reviewed_original_text LONGTEXT,

  CONSTRAINT fk_review_item
    FOREIGN KEY (item_id) REFERENCES knowledge_items(item_id)
    ON DELETE RESTRICT,

  CONSTRAINT chk_review_decision
    CHECK (decision IN ('approved', 'rejected')),

  INDEX idx_review_item_time (item_id, reviewed_at)
) ENGINE=InnoDB;
