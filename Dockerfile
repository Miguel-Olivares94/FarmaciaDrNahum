FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Archivos estáticos (sin base de datos)
RUN python manage.py collectstatic --noinput

# migrate y loaddata se ejecutan en runtime, no en build
CMD python manage.py migrate --noinput && \
    python manage.py loaddata datos_farmacia.json --ignorenonexistent && \
    gunicorn collico_sw.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
