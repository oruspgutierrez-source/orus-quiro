FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema requeridas para algunas librerias python si aplica
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando por defecto usando uvicorn con workers para producción (recomendado para balanceo de carga)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
