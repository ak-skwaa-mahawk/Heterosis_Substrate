FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt* ./
RUN pip install --no-cache-dir fastapi uvicorn websockets

COPY . .

EXPOSE 8000 43210/udp

ENTRYPOINT ["./run_node.sh"]
CMD ["node_primary", "8000"]
