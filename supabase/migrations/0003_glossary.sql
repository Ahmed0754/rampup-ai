-- Adds the personal glossary of jargon picked up from explanations (or added by hand).
-- Run this in the Supabase SQL editor if you set the project up before this table existed.

CREATE TABLE IF NOT EXISTS glossary_terms (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  term TEXT NOT NULL,
  definition TEXT NOT NULL,
  context TEXT,
  paste_id UUID REFERENCES pastes(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS glossary_terms_user_term_idx ON glossary_terms (user_id, lower(term));

ALTER TABLE glossary_terms ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users see own glossary" ON glossary_terms;
CREATE POLICY "Users see own glossary" ON glossary_terms FOR ALL USING (auth.uid() = user_id);
