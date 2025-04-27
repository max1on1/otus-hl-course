CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    first_name TEXT NOT NULL,
    second_name TEXT NOT NULL,
    birthdate DATE NOT NULL,
    biography TEXT,
    city TEXT,
    password_hash TEXT NOT NULL
);
