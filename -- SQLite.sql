-- SQLite
ALTER TABLE transcriptions ADD COLUMN audio_hash TEXT;
CREATE UNIQUE INDEX idx_audio_hash ON transcriptions (audio_hash);