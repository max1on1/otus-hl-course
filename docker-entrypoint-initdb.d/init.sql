BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    first_name TEXT NOT NULL,
    second_name TEXT NOT NULL,
    birthdate DATE NOT NULL,
    biography TEXT,
    city TEXT,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS friends (
    user_id    UUID NOT NULL,
    friend_id  UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (user_id, friend_id),
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_friend
        FOREIGN KEY(friend_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_name_prefix
  ON users (
    first_name text_pattern_ops,
    second_name text_pattern_ops
  );

CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY,
    author_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_posts_author_created
  ON posts (author_user_id, created_at DESC);

COMMIT;