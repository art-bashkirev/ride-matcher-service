FROM python:3.13-slim

# Install Doppler CLI
RUN apt-get update && apt-get --no-install-recommends install -y apt-transport-https ca-certificates curl gnupg && \
    curl -sLf --retry 3 --tlsv1.2 --proto '=https' --location-trusted 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && \
    apt-get -y --no-install-recommends install doppler \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade --no-cache-dir -r requirements.txt && \
    groupadd -r appuser && useradd -r -g appuser appuser

COPY . .
RUN chown -R appuser:appuser /app

EXPOSE 8080
USER appuser

ENTRYPOINT ["doppler", "run", "--"]

CMD ["python", "main.py"]