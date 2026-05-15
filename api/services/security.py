"""
Spec 09 — Módulo de Seguridad Centralizado
Contiene: sanitize_input(), check_rate_limit(), log_security_event()
"""

import re
import time
import unicodedata
from api.db.supabase_client import supabase

# ─────────────────────────────────────────────
# Rate Limiter In-Memory
# ─────────────────────────────────────────────
rate_limiter: dict[str, list[float]] = {}

RATE_LIMIT_WINDOW = 60   # segundos
RATE_LIMIT_THRESHOLD = 12  # mensajes máximos por ventana


# ─────────────────────────────────────────────
# Patrones de Amenaza (compilados una sola vez)
# ─────────────────────────────────────────────

# F3: Patrones SQLi clásicos
SQL_INJECTION_PATTERNS = re.compile(
    r"(?i)"
    r"("
    r"('\s*;\s*(DROP|ALTER|DELETE|UPDATE|INSERT|EXEC))"
    r"|(\bUNION\s+SELECT\b)"
    r"|(\bOR\s+1\s*=\s*1\b)"
    r"|(\bAND\s+1\s*=\s*1\b)"
    r"|(--\s)"
    r"|(/\*.*?\*/)"
    r"|(\bEXEC\s*\()"
    r"|(\bxp_\w+)"
    r")"
)

# F4: Patrones de Prompt Injection
PROMPT_INJECTION_PATTERNS = re.compile(
    r"(?i)"
    r"("
    r"(ignore\s+(all\s+)?previous\s+instructions)"
    r"|(you\s+are\s+now)"
    r"|(act\s+as\s+(a\s+)?)"
    r"|(system\s*prompt)"
    r"|(forget\s+(your|all)\s+rules)"
    r"|(new\s+instructions?\s*:)"
    r"|(disregard\s+(all\s+)?(above|prior))"
    r"|(override\s+(your\s+)?instructions)"
    r"|(do\s+not\s+follow\s+(your\s+)?rules)"
    r")"
)

# F2: Caracteres de control (excepto \n, \r, \t y espacio)
CONTROL_CHARS_PATTERN = re.compile(
    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]'
)

# Constantes
MAX_INPUT_LENGTH = 2000
MAX_RAW_PAYLOAD_LOG = 500


# ─────────────────────────────────────────────
# Función Principal: Sanitización de Entradas
# ─────────────────────────────────────────────

def sanitize_input(raw_text: str) -> tuple[str, bool, str | None]:
    """
    Pipeline de 5 etapas para limpiar texto entrante de WhatsApp.
    
    Retorna:
        (texto_limpio, threat_detected, threat_type)
        
    threat_type puede ser: 'SQL_INJECTION', 'PROMPT_INJECTION', 'UNICODE_ATTACK', None
    """
    if not raw_text:
        return ("", False, None)
    
    threat_detected = False
    threat_type = None
    text = raw_text

    # F5: Normalización Unicode (ANTES de los demás filtros para colapsar homóglifos)
    try:
        normalized = unicodedata.normalize('NFC', text)
        if normalized != text:
            threat_detected = True
            threat_type = 'UNICODE_ATTACK'
        text = normalized
    except Exception:
        pass  # Si falla la normalización, seguimos con el texto original

    # F1: Límite de longitud
    text = text[:MAX_INPUT_LENGTH]

    # F2: Eliminar caracteres de control
    text = CONTROL_CHARS_PATTERN.sub('', text)

    # F3: Detección de SQLi
    if SQL_INJECTION_PATTERNS.search(text):
        threat_detected = True
        threat_type = 'SQL_INJECTION'
        # Neutralizar: escapar comillas simples
        text = text.replace("'", "''")

    # F4: Detección de Prompt Injection
    if PROMPT_INJECTION_PATTERNS.search(text):
        threat_detected = True
        threat_type = 'PROMPT_INJECTION'
        # No descartamos el mensaje, pero el tipo queda registrado
        # Gemini ya está blindado con system_rules + Structured Outputs

    return (text.strip(), threat_detected, threat_type)


# ─────────────────────────────────────────────
# Rate Limiter (Anti-Spam)
# ─────────────────────────────────────────────

def check_rate_limit(sender_id: str) -> bool:
    """
    Verifica si un sender_id ha excedido el umbral de mensajes
    dentro de la ventana de tiempo.
    
    Retorna:
        True si el usuario DEBE SER BLOQUEADO (excedió el límite).
        False si está dentro de los límites normales.
    """
    now = time.time()
    
    if sender_id not in rate_limiter:
        rate_limiter[sender_id] = []
    
    # Filtrar timestamps dentro de la ventana activa
    rate_limiter[sender_id] = [
        ts for ts in rate_limiter[sender_id]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    
    # Verificar umbral
    if len(rate_limiter[sender_id]) >= RATE_LIMIT_THRESHOLD:
        return True  # BLOQUEADO
    
    # Registrar este mensaje
    rate_limiter[sender_id].append(now)
    return False  # OK


def clear_rate_limit(sender_id: str):
    """Limpia el historial de rate limit para un sender (usado en desbloqueo manual)."""
    rate_limiter.pop(sender_id, None)


# ─────────────────────────────────────────────
# Logging de Seguridad
# ─────────────────────────────────────────────

def log_security_event(
    severity: str,
    event_type: str,
    source: str,
    message: str,
    raw_payload: str | None = None
):
    """
    Inserta un evento de seguridad en la tabla orus_logs de Supabase.
    
    Args:
        severity: 'WARNING' o 'ERROR'
        event_type: 'SPAM_AUTOBLOCK', 'BLOCKED_REQUEST', 'PROMPT_INJECTION', etc.
        source: phone_number o IP del origen
        message: descripción legible del evento
        raw_payload: texto original (truncado a 500 chars)
    """
    try:
        payload = {
            'severity': severity,
            'event_type': event_type,
            'source_identifier': source,
            'error_message': message,
        }
        
        if raw_payload:
            payload['raw_payload'] = raw_payload[:MAX_RAW_PAYLOAD_LOG]
        
        supabase.table('orus_logs').insert(payload).execute()
    except Exception as e:
        # Fallback a consola si Supabase falla — nunca silenciar un log de seguridad
        print(f"[SECURITY] ERROR guardando log de seguridad: {e}", flush=True)
        print(f"[SECURITY] Evento perdido: {severity}/{event_type} de {source}: {message}", flush=True)
