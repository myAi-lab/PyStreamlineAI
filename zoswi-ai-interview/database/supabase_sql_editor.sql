CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interview_status') THEN
        CREATE TYPE interview_status AS ENUM ('in_progress', 'completed');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transcript_speaker') THEN
        CREATE TYPE transcript_speaker AS ENUM ('ai', 'candidate', 'system');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_name VARCHAR(200) NOT NULL,
    role VARCHAR(200) NOT NULL,
    interview_type VARCHAR(32) NOT NULL DEFAULT 'mixed',
    status interview_status NOT NULL DEFAULT 'in_progress',
    current_question TEXT NOT NULL DEFAULT '',
    turn_count INT NOT NULL DEFAULT 0,
    max_turns INT NOT NULL DEFAULT 5,
    transcript_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluation_signals JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE interview_sessions
    ADD COLUMN IF NOT EXISTS interview_type VARCHAR(32) NOT NULL DEFAULT 'mixed';

CREATE TABLE IF NOT EXISTS conversation_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    speaker transcript_speaker NOT NULL,
    message_text TEXT NOT NULL,
    sequence_no INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_transcript_sequence UNIQUE (session_id, sequence_no)
);

CREATE TABLE IF NOT EXISTS ai_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_order INT NOT NULL,
    question_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ai_question_order UNIQUE (session_id, question_order)
);

CREATE TABLE IF NOT EXISTS candidate_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES ai_questions(id) ON DELETE SET NULL,
    response_order INT NOT NULL,
    transcript_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_candidate_response_order UNIQUE (session_id, response_order)
);

CREATE TABLE IF NOT EXISTS evaluation_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES interview_sessions(id) ON DELETE CASCADE,
    technical_accuracy NUMERIC(4,2) NOT NULL DEFAULT 0,
    communication_clarity NUMERIC(4,2) NOT NULL DEFAULT 0,
    confidence NUMERIC(4,2) NOT NULL DEFAULT 0,
    overall_rating NUMERIC(4,2) NOT NULL DEFAULT 0,
    summary_text TEXT NOT NULL DEFAULT '',
    signals_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcripts_session_id ON conversation_transcripts(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_questions_session_id ON ai_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_candidate_responses_session_id ON candidate_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_summary_session_id ON evaluation_summary(session_id);
CREATE INDEX IF NOT EXISTS idx_app_settings_key ON app_settings(setting_key);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_interview_sessions_updated_at ON interview_sessions;
CREATE TRIGGER trg_interview_sessions_updated_at
BEFORE UPDATE ON interview_sessions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_evaluation_summary_updated_at ON evaluation_summary;
CREATE TRIGGER trg_evaluation_summary_updated_at
BEFORE UPDATE ON evaluation_summary
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_app_settings_updated_at ON app_settings;
CREATE TRIGGER trg_app_settings_updated_at
BEFORE UPDATE ON app_settings
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
