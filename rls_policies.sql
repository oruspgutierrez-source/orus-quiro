-- ====================================================================
-- Script: rls_policies.sql
-- Objetivo: Endurecimiento de Seguridad (Spec 08)
-- ====================================================================

-- 1. Habilitar Row Level Security (RLS) en todas las tablas críticas
ALTER TABLE public.orus_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orus_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orus_messages ENABLE ROW LEVEL SECURITY;

-- NOTA IMPORTANTE:
-- Al habilitar RLS, cualquier solicitud que provenga de un cliente con la clave 'anon'
-- o 'authenticated' será denegada por defecto a menos que exista una política explícita.
--
-- Dado que el backend de FastAPI utiliza la 'Service Role Key' (SUPABASE_KEY),
-- este bypassa automáticamente RLS, por lo que el servidor seguirá funcionando 
-- y teniendo acceso total (lectura/escritura) sin necesidad de políticas extra.

-- 2. (Opcional) Si el Dashboard React accede directamente usando la anon_key, 
-- descomentar y ajustar las siguientes líneas para permitir lectura autenticada:

-- CREATE POLICY "Permitir select a usuarios autenticados" 
-- ON public.orus_users FOR SELECT TO authenticated USING (true);

-- CREATE POLICY "Permitir select a usuarios autenticados" 
-- ON public.orus_logs FOR SELECT TO authenticated USING (true);

-- CREATE POLICY "Permitir select a usuarios autenticados" 
-- ON public.orus_messages FOR SELECT TO authenticated USING (true);
