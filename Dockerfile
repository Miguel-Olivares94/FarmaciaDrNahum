FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles

CMD ["/bin/bash", "-c", "echo '=== PASO 1: variables ===' && echo PORT=$PORT && echo '=== PASO 2: collectstatic ===' && python manage.py collectstatic --noinput && echo '=== PASO 3: migrate ===' && python manage.py migrate --noinput && echo '=== PASO 4: gunicorn ===' && exec gunicorn collico_sw.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 --access-logfile - --error-logfile -"]
