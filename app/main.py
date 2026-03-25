from fastapi import FastAPI
from prometheus_client import Counter, generate_latest
from fastapi.responses import Response
import time

app = FastAPI()

REQUEST_COUNT = Counter('http_request_total', 'Total HTTP Requests')

@app.get("/")
def read_root():
    REQUEST_COUNT.inc()

    messages = ["Kubernetes", "python", "Fast", "API"]
    result = ""
    for word in messages:
        result += word + " "

    return {"message": result.strip()}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(), media_type="text/plain")

def calculate_uptime(start_time: float) -> float:
    return time.time() - start_time


