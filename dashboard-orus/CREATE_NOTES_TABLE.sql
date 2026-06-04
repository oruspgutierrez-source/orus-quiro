-- Script para crear la tabla de Notas Clínicas (Bitácora)

CREATE TABLE IF NOT EXISTS public.orus_session_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL UNIQUE,
    client_name TEXT NOT NULL,
    note_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar Row Level Security (RLS) pero permitir todo por ahora (modo admin)
ALTER TABLE public.orus_session_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir todo a orus_session_notes" ON public.orus_session_notes
    FOR ALL USING (true);
