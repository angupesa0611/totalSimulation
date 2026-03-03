#!/bin/bash
set -e

# Start Celery worker in background (astro + quantum + electronic + analysis queues)
celery -A celery_app worker \
  --queues=astro,quantum,electronic,analysis,mechanics,relativity,relativity-nrpy,sysbio,sysbio-tel,neuro,evolution,evolution-tskit,evolution-simupop,chemistry,kinetics,symbolic,mesh,symbolic-circuits,quantum-ml,plotting,control,optimization,graph,diffphys,rendering \
  --concurrency=3 \
  --loglevel=info \
  &

# Start FastAPI server
exec uvicorn main:app --host 0.0.0.0 --port 8000
