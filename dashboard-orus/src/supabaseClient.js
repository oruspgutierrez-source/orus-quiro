import { createClient } from '@supabase/supabase-js';

// Usamos las variables de entorno de Vite o un fallback directo para asegurar que no falle en producción
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://rfwfveaudrnughtulbco.supabase.co';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_vhupF9kAOgV3GG-4TEMlPQ_jhqLPxY6';

export const supabase = createClient(supabaseUrl, supabaseKey);
