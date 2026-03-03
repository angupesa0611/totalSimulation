FROM manimcommunity/manim:latest

USER root
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1
USER manimuser

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=render-manim", "--concurrency=1", "--loglevel=info"]
