FROM python:3.8-slim-buster

ARG CELERY_FLOWER_PASSWORD
ARG DATABASE_URL
ARG DJANGO_SECRET_KEY
ARG EMAIL_HOST_PASSWORD
ARG POSTGRES_PASSWORD

ENV PYTHONUNBUFFERED 1
ENV DATABASE_URL $DATABASE_URL
ENV DJANGO_SECRET_KEY $DJANGO_SECRET_KEY
ENV EMAIL_HOST_PASSWORD $EMAIL_HOST_PASSWORD
ENV CELERY_FLOWER_PASSWORD $CELERY_FLOWER_PASSWORD
ENV POSTGRES_PASSWORD $POSTGRES_PASSWORD

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential nano \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django \
    && adduser --system --ingroup django django

# Requirements are installed here to ensure they will be cached.
COPY ./dauthenticator-Feature#3678/requirements /requirements
RUN pip install --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

# install twitter-driver, instagram-driver
RUN pip install --user --index-url https://kaisens:Kaizendata.2017@pypi.kaisens.fr/simple/ twitter_driver
RUN pip install --user --index-url https://kaisens:Kaizendatdockera.2017@pypi.kaisens.fr/simple/ instaDriver==0.4.5

COPY --chown=django:django ./dauthenticator-Feature#3678/compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint


COPY --chown=django:django ./dauthenticator-Feature#3678/compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:django . /app

USER django

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
