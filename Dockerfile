FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]