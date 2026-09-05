CREATE TABLE pastes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  raw_text TEXT NOT NULL,
  input_type TEXT NOT NULL,
  explanation TEXT,
  action_items JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE replies (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  paste_id UUID REFERENCES pastes(id) ON DELETE SET NULL,
  original_text TEXT NOT NULL,
  tone TEXT NOT NULL,
  reply_text TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE progress_entries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  entry_text TEXT NOT NULL,
  entry_type TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE weekly_summaries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  what_i_worked_on TEXT,
  what_i_learned TEXT,
  blockers TEXT,
  resume_bullets JSONB,
  talking_points TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE resume_bullets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  bullets JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE explain_chat_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  paste_id UUID REFERENCES pastes(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE pastes ENABLE ROW LEVEL SECURITY;
ALTER TABLE replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_bullets ENABLE ROW LEVEL SECURITY;
ALTER TABLE explain_chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own pastes" ON pastes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own replies" ON replies FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own progress" ON progress_entries FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own summaries" ON weekly_summaries FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own resume bullets" ON resume_bullets FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own explain chat" ON explain_chat_messages FOR ALL USING (auth.uid() = user_id);
