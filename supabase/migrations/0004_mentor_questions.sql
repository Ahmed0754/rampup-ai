-- Adds the list of questions to bring to a mentor / manager 1:1.
-- Run this in the Supabase SQL editor if you set the project up before this table existed.

CREATE TABLE IF NOT EXISTS mentor_questions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  context TEXT,
  paste_id UUID REFERENCES pastes(id) ON DELETE SET NULL,
  answer TEXT,
  answered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE mentor_questions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users see own mentor questions" ON mentor_questions;
CREATE POLICY "Users see own mentor questions" ON mentor_questions FOR ALL USING (auth.uid() = user_id);
