-- Adds persistence for follow-up questions on an Explain result.
-- Run this in the Supabase SQL editor if you set the project up before this table existed.

CREATE TABLE IF NOT EXISTS explain_chat_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  paste_id UUID REFERENCES pastes(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE explain_chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users see own explain chat" ON explain_chat_messages;
CREATE POLICY "Users see own explain chat" ON explain_chat_messages FOR ALL USING (auth.uid() = user_id);
