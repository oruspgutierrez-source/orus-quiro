# Spec 29: Integración de Datos Biométricos en el Dashboard

## Objetivo
Reemplazar la sección "Security" del Dashboard con un nuevo módulo "Biometría" (o "Evaluaciones"). Este módulo permitirá listar las evaluaciones recibidas en la tabla `evaluaciones_completas` y descargar las imágenes asociadas a cada evaluación empaquetadas en un archivo ZIP, nombrado automáticamente con el nombre del paciente.

## Análisis Técnico y Recomendación sobre el ZIP

Para descargar las imágenes en formato ZIP, tenemos dos enfoques principales. **Te recomiendo encarecidamente la Opción 1**:

1. **Crear el ZIP en el Frontend (Dashboard) con JS - RECOMENDADO**
   - **Cómo funciona:** El dashboard (React) utiliza el cliente de Supabase para descargar las imágenes directamente desde el bucket al navegador del usuario (como datos binarios/Blobs). Luego, usa una librería como `jszip` para crear el archivo ZIP localmente en la computadora del administrador y lanza la descarga.
   - **Por qué es mejor:** Libera de toda esta carga a nuestra VPS. Empaquetar imágenes requiere memoria y CPU; hacerlo en el navegador del usuario final es la práctica estándar en paneles modernos de administración. Además, ya tienes las credenciales de Supabase en el Dashboard.

2. **Crear el ZIP en el Backend (FastAPI o Supabase Edge Functions)**
   - **Cómo funciona:** Creariamos una ruta en FastAPI que descargue las imágenes, arme el ZIP en memoria RAM del servidor y lo envíe de vuelta al dashboard.
   - **Por qué NO lo recomiendo:** Podría saturar la memoria de nuestra VPS en EasyPanel si varios usuarios descargan imágenes pesadas al mismo tiempo.

## Plan de Trabajo (Task by Task)

### Task 1: Preparación y Definición de Estructura (Tu turno)
Necesito que me confirmes lo siguiente para poder empezar:
1. **¿Estás de acuerdo con usar la Opción 1 (Frontend)?**
2. **¿Cómo relacionamos las imágenes con el usuario?**
   - ¿Las rutas de las imágenes están guardadas en alguna columna dentro de la tabla `evaluaciones_completas`? (Ej. una columna tipo JSON/Array).
   - O bien, ¿se suben a una carpeta específica en el bucket `biometria_test` que lleva el nombre del `id` o `wa_id` del usuario? (Ej. `biometria_test/usuario_web_1779463260370/foto1.jpg`).

### Task 2: UI Base y Navegación
- Reemplazar "Security" en el menú de navegación (`Sidebar`) por "Evaluaciones" o "Biometría".
- Crear el esqueleto de la vista `BiometricView.jsx`.

### Task 3: Integración de la Tabla
- Conectar `BiometricView.jsx` a la tabla `evaluaciones_completas` de Supabase.
- Mostrar una tabla limpia y profesional con los datos del formulario (Nombre, Creado en, ID, etc.).

### Task 4: Funcionalidad de Descarga en ZIP
- Instalar `jszip` y `file-saver` en el proyecto del Dashboard.
- Crear el script dentro del dashboard que, al hacer clic en un botón de "Descargar ZIP" en la tabla, obtenga las imágenes de ese usuario específico.
- Empaquetar y nombrar el archivo dinámicamente: `[Nombre del Paciente]_Evaluacion.zip`.
