-- Fuck me
-- Create citext extension
CREATE TABLE IF NOT EXISTS settings (
  guild_id BIGINT NOT NULL,
  prefixes TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
  PRIMARY KEY (guild_id)
);

-- economy balance
CREATE TABLE IF NOT EXISTS economy (
  user_id BIGINT    PRIMARY KEY,
  wallet  BIGINT    NOT NULL DEFAULT 0,
  bank    BIGINT    NOT NULL DEFAULT 0
);
