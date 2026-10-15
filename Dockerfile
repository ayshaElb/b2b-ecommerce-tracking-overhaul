FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "02_gtm_serverside.gtm_ss_proxy_server:app", "--host", "0.0.0.0", "--port", "8080"]
