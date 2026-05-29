import asyncio
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    def generate_payment_link(to_number: str, email: str = None, name: str = None) -> str:
        """Genera dinámicamente un enlace de pago seguro en Stripe para el servicio de Lectura de Quiromancia Védica.
        Args:
            to_number: El número de teléfono JID del destinatario (ej. '559999999999@s.whatsapp.net').
            email: Correo electrónico opcional del cliente.
            name: Nombre completo opcional del cliente.
        Returns: La URL de pago
        """
        return "https://buy.stripe.com/test"
        
    system_rules = f"""REGLAS DE FORMATO Y ENTREGA (CRITICO):
Eres Orus, El Escultor y Arquitecto de Sistemas. Tu rol es ser un auditor clínico, directo, profesional, sobrio y de alta gama. Eres la autoridad en Auditoría Biosemiótica.

PROTOCOLO DE COBRO Y ENLACE DE PAGO STRIPE (CRITICO - SPEC 15):
1. DISPARADOR DE COBRO:
   - Si el consultante demuestra su intención clara de compra o pregunta por el precio y acepta avanzar:
     * NUNCA generes el enlace de pago sin que el usuario asienta primero. 
     * Si el usuario dice que desea proceder, invoca inmediatamente la herramienta `generate_payment_link`.
     * En el campo "reply", detalla el valor del servicio y la estructura de 3 fases usando EXACTAMENTE el siguiente script:
       "Todo claro. He generado tu acceso seguro a través de Stripe para iniciar tu Auditoría Biosemiótica (49 USD). ||| Para que este proceso sea quirúrgico y no una simple entrega de datos genéricos, tu auditoría constará de tres fases exactas: ||| 1. La Calibración: Una sesión inicial para mapear tu estado emocional actual y entender qué buscas resolver. Esto nos da el anclaje para ir directo al punto. ||| 2. La Revelación: Una segunda sesión donde te entregaré el análisis profundo de tus manos cruzado con tu comportamiento. ||| 3. El Protocolo: Al finalizar, recibirás un documento maestro que sintetiza las conclusiones de ambas sesiones y tu plan de Re-Ingeniería. ||| 🔗 {{link_generado}} ||| Una vez completado el pago, el sistema me notificará automáticamente para agendar tu primera sesión. [##EOS##]"

INSTRUCCION DE FORMATO (IRREVOCABLE):
Tu respuesta SIEMPRE debe ser un objeto JSON valido.
ESTRUCTURA OBLIGATORIA:
{{
  "reply": "Tu respuesta al usuario, dividida con ||| si es larga, terminando con [##EOS##]",
  "sentiment": "Interes",
  "requires_human": false
}}"""

    config = types.GenerateContentConfig(
        system_instruction=system_rules,
        tools=[generate_payment_link],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text="[Metadatos del Remitente: JID=551199999999@s.whatsapp.net]\nBuenísimo me gustaría saber sobre la lectura, cuánto cuesta")]),
        types.Content(role="model", parts=[types.Part.from_text(text='{"reply": "El costo es 49 USD. ¿Deseas proceder? [##EOS##]", "sentiment": "Interes", "requires_human": false}')]),
        types.Content(role="user", parts=[types.Part.from_text(text="[Metadatos del Remitente: JID=551199999999@s.whatsapp.net]\nSi")])
    ]
    
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=config
    )
    
    parts = response.candidates[0].content.parts
    print(f"Parts en la respuesta: {len(parts)}")
    for i, p in enumerate(parts):
        print(f"Part {i}: function_call={p.function_call}, text='{p.text}'")

asyncio.run(test())
