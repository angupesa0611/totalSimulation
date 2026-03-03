FROM python:3.11-slim

RUN pip install --no-cache-dir qiskit qiskit-aer celery[redis]==5.4.0 redis==5.2.1 numpy

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=circuits-qiskit", "--concurrency=1", "--loglevel=info"]
