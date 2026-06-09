import re
import unicodedata
from datetime import datetime, time, date
from zoneinfo import ZoneInfo
import collections
from typing import Optional, Tuple, Dict, List

# Demonyms, cities, and countries mapping to standard IANA timezone keys
COUNTRY_TIMEZONE_MAP = {
    "espana": "Europe/Madrid",
    "colombia": "America/Bogota",
    "mexico": "America/Mexico_City",
    "peru": "America/Lima",
    "ecuador": "America/Guayaquil",
    "chile": "America/Santiago",
    "argentina": "America/Argentina/Buenos_Aires",
    "uruguay": "America/Montevideo",
    "venezuela": "America/Caracas",
    "bolivia": "America/La_Paz",
    "paraguay": "America/Asuncion",
    "panama": "America/Panama",
    "costa rica": "America/Costa_Rica",
    "honduras": "America/Tegucigalpa",
    "guatemala": "America/Guatemala",
    "el salvador": "America/El_Salvador",
    "nicaragua": "America/Managua",
    "republica dominicana": "America/Santo_Domingo",
    "dominicana": "America/Santo_Domingo",
    "cuba": "America/Havana",
    "puerto rico": "America/Puerto_Rico",
}

COUNTRY_KEYWORDS = {
    "espana": ["espana", "madrid", "barcelona", "valencia", "sevilla", "espanol", "espanola"],
    "colombia": ["colombia", "bogota", "medellin", "cali", "barranquilla", "colombiano", "colombiana"],
    "mexico": ["mexico", "cdmx", "guadalajara", "monterrey", "mexicano", "mexicana"],
    "peru": ["peru", "lima", "arequipa", "peruano", "peruana"],
    "ecuador": ["ecuador", "quito", "guayaquil", "ecuatoriano", "ecuatoriana"],
    "chile": ["chile", "santiago", "chileno", "chilena"],
    "argentina": ["argentina", "buenos aires", "rosario", "cordoba", "argentino", "argentina"],
    "uruguay": ["uruguay", "montevideo", "uruguayo", "uruguaya"],
    "venezuela": ["venezuela", "caracas", "maracaibo", "venezolano", "venezolana"],
    "bolivia": ["bolivia", "la paz", "sucre", "boliviano", "boliviana"],
    "paraguay": ["paraguay", "asuncion", "paraguayo", "paraguaya"],
    "panama": ["panama", "panameno", "panamena"],
    "costa rica": ["costa rica", "san jose", "costarricense"],
    "honduras": ["honduras", "tegucigalpa", "hondureno", "hondurena"],
    "guatemala": ["guatemala", "guatemalteco", "guatemalteca"],
    "el salvador": ["el salvador", "san salvador", "salvadoreno", "salvadorena"],
    "nicaragua": ["nicaragua", "managua", "nicaraguense"],
    "republica dominicana": ["republica dominicana", "santo domingo", "dominicano", "dominicana"],
    "cuba": ["cuba", "habana", "cubano", "cubana"],
    "puerto rico": ["puerto rico", "san juan", "puertorriqueno", "puertorriquena"]
}

def normalize_text(text: str) -> str:
    """Convierte el texto a minúsculas y elimina acentos/diacríticos."""
    if not text:
        return ""
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

def detect_country_and_timezone(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Analiza el texto de entrada y detecta si corresponde a alguno de los países mapeados.
    Retorna una tupla (nombre_pais, zona_horaria_iana) o (None, None) si no se detecta.
    """
    normalized = normalize_text(text)
    
    # Intentar buscar palabras clave asociadas a cada país
    for country_key, keywords in COUNTRY_KEYWORDS.items():
        for kw in keywords:
            # Búsqueda exacta de palabra clave como límite de palabra
            pattern = rf"\b{kw}\b"
            if re.search(pattern, normalized):
                # Encontrar el nombre formateado del país
                formal_name = country_key.capitalize()
                if formal_name == "Espana":
                    formal_name = "España"
                elif formal_name == "Republica dominicana":
                    formal_name = "República Dominicana"
                
                timezone = COUNTRY_TIMEZONE_MAP[country_key]
                return formal_name, timezone
                
    return None, None

def get_user_localized_slots(therapist_slots: Dict[str, List[int]], user_timezone: str) -> Dict[str, List[Dict]]:
    """
    Toma la disponibilidad del terapeuta (en America/Sao_Paulo) y la convierte a la zona horaria del usuario.
    Aplica filtros de horario adaptativos (ej. España: ocultar después de 10 PM local; Latam: ocultar antes de 7 AM local).
    
    therapist_slots: dict tipo {"2026-06-12": [8, 9, 10, 11, 13, 15, 16, 17, 18, 19, 20]}
    
    Retorna un diccionario indexado por fecha local del usuario (YYYY-MM-DD) conteniendo una lista de slots.
    Cada slot es un dict: {
        "local_hour": int,
        "local_time_str": str, (ej. "8:00 am", "3:00 pm")
        "sp_iso": str, (fecha/hora en formato ISO de Sao Paulo)
        "sp_hour": int
    }
    """
    tz_sp = ZoneInfo("America/Sao_Paulo")
    try:
        tz_user = ZoneInfo(user_timezone)
    except Exception:
        tz_user = ZoneInfo("America/Bogota") # Fallback seguro

    localized_slots = collections.defaultdict(list)

    for date_str, hours in therapist_slots.items():
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            continue
            
        for hour in hours:
            # Combinar fecha y hora en el huso horario de Sao Paulo (el del terapeuta)
            dt_sp = datetime.combine(parsed_date, time(hour, 0), tzinfo=tz_sp)
            # Convertir a la zona horaria local del consultante
            dt_user = dt_sp.astimezone(tz_user)

            user_date_str = dt_user.strftime("%Y-%m-%d")
            user_hour = dt_user.hour

            # Formatear el indicador am/pm en español/inglés legible
            if user_hour == 0:
                time_str = "12:00 am"
            elif user_hour < 12:
                time_str = f"{user_hour}:00 am"
            elif user_hour == 12:
                time_str = "12:00 pm"
            else:
                time_str = f"{user_hour - 12}:00 pm"

            # Aplicar filtros de horarios cómodos para el cliente
            if "Europe/Madrid" in user_timezone:
                # Ocultar citas posteriores a las 10 PM (22:00) o de madrugada en España
                if user_hour >= 22 or user_hour < 8:
                    continue
            elif "America/Mexico_City" in user_timezone or "America/Bogota" in user_timezone or "America/Lima" in user_timezone or "America/Guayaquil" in user_timezone:
                # Ocultar citas anteriores a las 7:00 AM en LATAM
                if user_hour < 7 or user_hour >= 22:
                    continue
            else:
                # Límite por defecto seguro para cualquier otro país
                if user_hour < 7 or user_hour >= 22:
                    continue

            localized_slots[user_date_str].append({
                "local_hour": user_hour,
                "local_time_str": time_str,
                "sp_iso": dt_sp.strftime("%Y-%m-%dT%H:%M:%S-03:00"),
                "sp_hour": hour
            })

    # Ordenar los días por fecha y las horas por hora local
    sorted_slots = {}
    for d_str in sorted(localized_slots.keys()):
        sorted_slots[d_str] = sorted(localized_slots[d_str], key=lambda x: x["local_hour"])

    return sorted_slots

MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def format_localized_availability(localized_slots: Dict[str, List[Dict]], user_timezone: str) -> str:
    """
    Formatea la disponibilidad localizada en un mensaje legible y amigable de WhatsApp.
    """
    lines = ["Estos son los horarios disponibles para tu sesión de Mapeo en tu hora local:"]

    if not localized_slots:
        return "No tengo horarios disponibles en este momento que se ajusten a tus horas hábiles locales. Por favor, avísame si prefieres revisar opciones fuera de tu horario habitual."

    for day_str in sorted(localized_slots.keys()):
        try:
            parsed = datetime.strptime(day_str, "%Y-%m-%d")
            day_name = DAYS_ES[parsed.weekday()]
            day_num = parsed.day
            month_name = MONTHS_ES[parsed.month - 1]
            label = f"{day_name} {day_num} de {month_name}"
        except Exception:
            label = day_str

        slots = localized_slots[day_str]
        am_slots = [s["local_time_str"] for s in slots if s["local_hour"] < 12]
        pm_slots = [s["local_time_str"] for s in slots if s["local_hour"] >= 12]

        day_line = f"\n🟢 *{label}*:"
        if am_slots:
            day_line += f"\n  Mañana: {', '.join(am_slots)}"
        if pm_slots:
            day_line += f"\n  Tarde/Noche: {', '.join(pm_slots)}"
        lines.append(day_line)

    lines.append("\n¿Qué día y horario te queda mejor? (Indícame el día y la hora)")
    return "\n".join(lines)

def get_next_5_active_days() -> List[str]:
    """Calcula los siguientes 5 días activos (lunes a sábado) a partir de mañana.
    Retorna una lista de strings con formato 'YYYY-MM-DD'.
    """
    import datetime as dt
    days = []
    current = dt.date.today() + dt.timedelta(days=1)
    while len(days) < 5:
        # 0 = lunes, ..., 5 = sábado, 6 = domingo
        if current.weekday() < 6:
            days.append(current.strftime("%Y-%m-%d"))
        current += dt.timedelta(days=1)
    return days

def find_matching_date(text: str, cached_slots: dict) -> Optional[str]:
    """
    Identifica la fecha en cached_slots (YYYY-MM-DD) que el usuario menciona en su mensaje,
    ya sea por número de día (ej: "12") o por nombre de día (ej: "viernes").
    """
    normalized = normalize_text(text)
    
    # Mapear nombres de días a su número de día de la semana (0 = lunes, ..., 6 = domingo)
    weekday_map = {
        "lunes": 0,
        "martes": 1,
        "miercoles": 2,
        "jueves": 3,
        "viernes": 4,
        "sabado": 5,
        "domingo": 6
    }
    
    # 1. Buscar números en el texto que correspondan a días del mes
    numbers = re.findall(r'\b([1-9]|[12]\d|3[01])\b', normalized)
    
    if numbers:
        for num in numbers:
            for date_str in cached_slots.keys():
                try:
                    dt_val = datetime.strptime(date_str, "%Y-%m-%d")
                    if dt_val.day == int(num):
                        return date_str
                except Exception:
                    continue
                    
    # 2. Buscar nombres de días de la semana
    for day_name, weekday_int in weekday_map.items():
        if day_name in normalized:
            for date_str in cached_slots.keys():
                try:
                    dt_val = datetime.strptime(date_str, "%Y-%m-%d")
                    if dt_val.weekday() == weekday_int:
                        return date_str
                except Exception:
                    continue
                    
    return None

def find_matching_slot(text: str, slots: List[Dict], matched_date: Optional[str] = None) -> Optional[Dict]:
    """
    Busca si en la lista de slots disponibles para un día hay alguno que coincida
    con la hora especificada por el usuario.
    """
    normalized = normalize_text(text)
    
    # Detectar si se menciona PM o AM
    is_pm = any(p in normalized for p in ["pm", "tarde", "noche"])
    is_am = any(a in normalized for a in ["am", "manana"])
    
    # Buscar patrones de hora tipo "15:00" o "3:00"
    time_matches = re.findall(r'\b(\d{1,2})\s*:\s*(\d{2})\b', normalized)
    if time_matches:
        for hr_str, min_str in time_matches:
            hr = int(hr_str)
            if hr < 12 and is_pm:
                hr += 12
            for slot in slots:
                if slot["local_hour"] == hr:
                    return slot
            # Si no hay coincidencia exacta de hora, pero coincide el número de hora
            for slot in slots:
                if abs(slot["local_hour"] - hr) == 0:
                    return slot

    # Buscar números individuales que representen la hora
    numbers = [int(n) for n in re.findall(r'\b(\d{1,2})\b', normalized)]
    
    # Si tenemos matched_date, excluir el día del mes para evitar falsos positivos de hora (ej: "15 de junio a las 8")
    exclude_day = None
    if matched_date:
        try:
            exclude_day = datetime.strptime(matched_date, "%Y-%m-%d").day
        except Exception:
            pass

    for num in numbers:
        if exclude_day is not None and num == exclude_day:
            continue
        # Una hora hábil razonable suele estar entre 1 y 23.
        if num < 1 or num > 23:
            continue
            
        hr_candidate = num
        if hr_candidate < 12 and is_pm:
            hr_candidate += 12
        elif hr_candidate == 12 and is_am:
            hr_candidate = 0
            
        # Comprobar coincidencia exacta
        for slot in slots:
            if slot["local_hour"] == hr_candidate:
                return slot
                
        # Si el usuario no especificó AM/PM, comprobar ambas opciones (ej: "a las 3" puede ser 15:00)
        if not is_am and not is_pm:
            for slot in slots:
                if hr_candidate < 12:
                    if slot["local_hour"] == hr_candidate or slot["local_hour"] == hr_candidate + 12:
                        return slot
                        
    return None
