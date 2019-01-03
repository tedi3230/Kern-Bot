CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS submissions (
    contest_id UUID NOT NULL,
    author_id BIGINT NOT NULL,
    title VARCHAR[100] NOT NULL,
    description VARCHAR[2000] NOT NULL,
    image_url VARCHAR[],
    rating INTEGER,
    CONSTRAINT one_submission_per_content
      PRIMARY KEY (contest_id, author_id)
);

CREATE TABLE IF NOT EXISTS contests (
    contest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    contest_name TEXT,
    channel_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    submission_channel_id BIGINT,
    prefixes TEXT[],
    max_rating INTEGER DEFAULT 10
);
