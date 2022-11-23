FROM git.kaisens.fr:5050/drivers/dauthenticator/web:latest as builder
USER root
ARG DJANGO_SETTINGS_MODULE=config.settings.production
RUN python manage.py collectstatic --noinput

FROM nginx:1.19.0-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY ./compose/production/nginx/default.conf /etc/nginx/conf.d
COPY --from=builder /app/staticfiles /app/staticfiles
EXPOSE 80
