-- +goose Up
-- +goose StatementBegin

-- Model registry
CREATE TABLE models (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT NOT NULL,                       -- openai, anthropic, deepseek, openrouter
    model_id        TEXT NOT NULL UNIQUE,                -- gpt-4o, claude-3.5-sonnet, deepseek/deepseek-chat-v4-flash
    display_name    TEXT,
    input_cost      REAL,                                -- cost per 1M input tokens
    output_cost     REAL,                                -- cost per 1M output tokens
    context_window  INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Prompt templates with versioning
CREATE TABLE prompts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,                       -- classify-essay, extract-entity, summarize
    version         INTEGER NOT NULL DEFAULT 1,
    system_prompt   TEXT NOT NULL,
    user_template   TEXT,                                -- template string with {placeholders}
    model_id        TEXT REFERENCES models(model_id),
    temperature     REAL DEFAULT 0.1,
    max_tokens      INTEGER DEFAULT 1024,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, version)
);

-- Evaluation fixtures
CREATE TABLE eval_fixtures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,                -- sample_extraction, essay-classify-3
    description     TEXT,
    input_count     INTEGER NOT NULL DEFAULT 0,
    path            TEXT,                                -- relative path to fixture file
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Evaluation runs
CREATE TABLE eval_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id      INTEGER REFERENCES eval_fixtures(id),
    prompt_id       INTEGER REFERENCES prompts(id),
    model_id        TEXT REFERENCES models(model_id),
    total_tests     INTEGER NOT NULL DEFAULT 0,
    passed          INTEGER NOT NULL DEFAULT 0,
    failed          INTEGER NOT NULL DEFAULT 0,
    avg_score       REAL,
    total_tokens    INTEGER,
    total_cost      REAL,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT
);

-- Individual evaluation results
CREATE TABLE eval_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
    input_index     INTEGER NOT NULL,
    input_summary   TEXT,
    expected        TEXT,
    actual          TEXT,
    score           REAL,
    passed          INTEGER NOT NULL DEFAULT 0,
    tokens_used     INTEGER,
    latency_ms      INTEGER,
    error_message   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Benchmark tasks
CREATE TABLE benchmark_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,                -- mmlu, humaneval, custom-qa
    description     TEXT,
    category        TEXT,                                -- reasoning, coding, knowledge, classification
    metric          TEXT NOT NULL DEFAULT 'accuracy',    -- accuracy, f1, bleu, rouge
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Benchmark runs
CREATE TABLE benchmark_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER REFERENCES benchmark_tasks(id),
    model_id        TEXT REFERENCES models(model_id),
    score           REAL NOT NULL,
    total_tests     INTEGER NOT NULL DEFAULT 0,
    tokens_used     INTEGER,
    total_cost      REAL,
    notes           TEXT,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT
);

-- Extraction worker runs
CREATE TABLE extraction_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_name     TEXT NOT NULL,                       -- entity-extractor, date-parser
    document_path   TEXT NOT NULL,
    document_hash   TEXT,
    model_id        TEXT REFERENCES models(model_id),
    prompt_id       INTEGER REFERENCES prompts(id),
    result_json     TEXT,
    confidence      REAL,
    tokens_used     INTEGER,
    cost            REAL,
    error_message   TEXT,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT
);

-- Essay classifications (from classify pipeline)
CREATE TABLE essay_classifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL,
    relative_path   TEXT,
    title           TEXT,
    word_count      INTEGER,
    domains_json    TEXT NOT NULL,                       -- JSON array of domain tags
    confidence      REAL,
    reasoning       TEXT,
    needs_review    INTEGER NOT NULL DEFAULT 0,
    model_id        TEXT REFERENCES models(model_id),
    classified_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX idx_eval_runs_fixture ON eval_runs(fixture_id);
CREATE INDEX idx_eval_runs_model ON eval_runs(model_id);
CREATE INDEX idx_eval_results_run ON eval_results(run_id);
CREATE INDEX idx_benchmark_runs_task ON benchmark_runs(task_id);
CREATE INDEX idx_benchmark_runs_model ON benchmark_runs(model_id);
CREATE INDEX idx_extraction_runs_worker ON extraction_runs(worker_name);
CREATE INDEX idx_essay_classifications_domain ON essay_classifications(confidence);

-- Seed known models
INSERT OR IGNORE INTO models (provider, model_id, display_name) VALUES
    ('deepseek', 'deepseek/deepseek-chat-v4-flash', 'DeepSeek V4 Flash'),
    ('anthropic', 'anthropic/claude-3.5-haiku', 'Claude 3.5 Haiku'),
    ('anthropic', 'anthropic/claude-3.5-sonnet', 'Claude 3.5 Sonnet'),
    ('openai', 'openai/gpt-4o-mini', 'GPT-4o Mini'),
    ('openai', 'openai/gpt-4o', 'GPT-4o');

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS essay_classifications;
DROP TABLE IF EXISTS extraction_runs;
DROP TABLE IF EXISTS benchmark_runs;
DROP TABLE IF EXISTS benchmark_tasks;
DROP TABLE IF EXISTS eval_results;
DROP TABLE IF EXISTS eval_runs;
DROP TABLE IF EXISTS eval_fixtures;
DROP TABLE IF EXISTS prompts;
DROP TABLE IF EXISTS models;
-- +goose StatementEnd
