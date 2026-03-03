FROM sagemath/sagemath:latest

USER root
RUN sage -pip install celery[redis]==5.4.0 redis==5.2.1
USER sage

WORKDIR /app
COPY . .

CMD ["sage", "-python", "-m", "celery", "-A", "worker", "worker", "--queues=math-sage", "--concurrency=1", "--loglevel=info"]
