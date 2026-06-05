# Spec 29: Integración de Datos Biométricos en el Dashboard

## Objetivo (Logrado)
Reemplazar la antigua sección "Security" del Dashboard con un nuevo módulo "Biometría" para gestionar las evaluaciones de los pacientes. Este módulo permite listar las evaluaciones recibidas en la tabla `evaluaciones_completas`, verificar su estado, previsualizar las fotos en un panel lateral (Drawer) y descargar las imágenes junto a notas clínicas en un archivo ZIP nombrado automáticamente.

## Arquitectura Implementada

Se optó por la **creación del ZIP en el Frontend (Dashboard) con JS**.
- **Cómo funciona:** El dashboard (React) utiliza el cliente de Supabase para obtener las URLs de las imágenes y descargar sus datos binarios. Usa `jszip` y `file-saver` para armar el archivo ZIP directamente en el navegador del administrador.
- **Ventaja:** Libera a la VPS de tareas pesadas (CPU/Memoria), trasladando el procesamiento gráfico y de empaquetado al cliente.

## Funcionalidades Completadas

### 1. UI Base y Navegación
- Se reemplazó "Security" por "Biometría" en `AppLayout.jsx`.
- Se creó `BiometricView.jsx` con diseño Dark Mode Premium, empleando `glassCard` y un Layout estructurado tipo cuadrícula (Grid) para mostrar las tarjetas de pacientes.

### 2. Integración de Supabase y Tabla
- Se conectó `BiometricView` a `evaluaciones_completas` para traer los datos reales de los pacientes.
- Se implementó una lógica de escaneo asíncrono (`checkBuckets`) que verifica en tiempo real la conexión con el bucket de Storage y detecta si existen archivos en el folder (`wa_id`) de cada usuario.

### 3. Indicadores de Estado de los Datos (Status Dots)
- **Punto Amarillo:** Bucket verificado y contiene imágenes.
- **Punto Rojo:** No se encontraron imágenes o la carpeta no existe, indicando que se debe volver a subir.
- *Resolución de Bugs:* Se aplicó `flex-1 min-w-0` en el contenedor del nombre/ID para activar correctamente el `truncate` de Tailwind y evitar que IDs largos empujen el indicador de estado fuera de la tarjeta.

### 4. Drawer de Previsualización y Notas
- En vez de descargar a ciegas, el administrador hace clic en "Ver Detalles y Fotos".
- Se despliega un panel flotante lateral oscuro (Drawer) donde puede ver:
  - Información personal completa.
  - Una galería de previsualización de las imágenes cargadas utilizando Signed URLs por motivos de seguridad.
  - Un cuadro de texto para incluir las **Notas del Doctor**.

### 5. Empaquetado Automático en ZIP
- Al exportar, el Dashboard reúne:
  1. Todas las fotos del bucket correspondientes al paciente.
  2. Un archivo generado en vivo `datos_paciente.txt` que incluye toda la información del paciente extraída de la tabla y las "Notas del Doctor" que se escribieron en la interfaz.
- El ZIP se descarga nominado bajo la convención: `[Nombre del Paciente]_Evaluacion.zip`.

## Consideraciones Futuras
- **Vercel vs VPS:** Se determinó mantener la App de recolección biométrica en Vercel por su alto rendimiento y CDN global.
- **Registro de Errores Frontend:** En caso de fallos en la App Biométrica, los errores serán enviados directamente a la tabla `orus_logs` en Supabase para que sean monitorizados desde la pestaña "System Logs" del Dashboard actual, unificando todo el centro de comando en un solo lugar sin necesidad de tablas nuevas.
- **Política de Supabase:** Se configuró en Supabase la política (RLS) `Allow public SELECT` en `storage.objects` (con `bucket_id = biometria_test`) para garantizar que el Dashboard pueda escanear y cargar la galería exitosamente usando la clave anónima.
