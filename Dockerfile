FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8080

CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:8080", "mt5_rest:app"]
