FROM python:3.9

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_DEBUG=True
ENV FLASK_APP=app.py
ENV REDIS_URL=redis://host.docker.internal
ENV DB_HOST=host.docker.internal
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres
ENV DB_PORT=5432
ENV DB_NAME=api8inf349
ENV PYTHONUNBUFFERED=1

CMD ["flask", "run", "--host", "0.0.0.0"]