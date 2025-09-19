FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade --no-cache-dir -r requirements.txt && \
    groupadd -r appuser && useradd -r -g appuser appuser

COPY . .
RUN chown -R appuser:appuser /app

EXPOSE 8080
USER appuser

CMD ["python", "main.py"]