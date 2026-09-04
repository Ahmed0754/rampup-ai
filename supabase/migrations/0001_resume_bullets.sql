-- Adds persistence for the Resume Bullets feature.
-- Run this in the Supabase SQL editor if you set the project up before this table existed.

CREATE TABLE IF NOT EXISTS resume_bullets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  bullets JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE resume_bullets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users see own resume bullets" ON resume_bullets;
CREATE POLICY "Users see own resume bullets" ON resume_bullets FOR ALL USING (auth.uid() = user_id);
