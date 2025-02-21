ARG IMAGE_BASE_URL="releases.registry.docker.kaisens.fr"
ARG PYTHON_IMAGE_VERSION="3.10-3"
ARG PYTHON_BUILD_IMAGE_VERSION="${PYTHON_IMAGE_VERSION}-3"
ARG BUILD_ENVIRONMENT="prod"

ARG TMP_SETUP_DIRPATH="/tmp/src"
ARG VENV_DIRPATH="/opt/venv"
ARG APP_HOME="/app"


FROM ${IMAGE_BASE_URL}/kaisensdata/devops/docker-images/python-build:${PYTHON_BUILD_IMAGE_VERSION} as builder

ARG VENV_DIRPATH
ARG TMP_SETUP_DIRPATH
ARG BUILD_ENVIRONMENT

USER root

RUN virtualenv "${VENV_DIRPATH}"
COPY requirements/ "${TMP_SETUP_DIRPATH}/requirements"

RUN "${VENV_DIRPATH}"/bin/pip install --no-cache-dir -r "${TMP_SETUP_DIRPATH}/requirements/${BUILD_ENVIRONMENT}" \
	&& "${VENV_DIRPATH}"/bin/pip install --no-cache-dir -r "${TMP_SETUP_DIRPATH}/requirements/docs" \
	;

USER "${OPS_USER}"


FROM ${IMAGE_BASE_URL}/kaisensdata/devops/docker-images/python:${PYTHON_IMAGE_VERSION} as run

ARG APP_HOME
ARG VENV_DIRPATH
ARG BUILD_ENVIRONMENT

WORKDIR "${APP_HOME}/docs"

USER root

COPY --from=builder --chown="${OPS_USER}":"${OPS_USER}" "${VENV_DIRPATH}" "${VENV_DIRPATH}"

ENV PATH="${VENV_DIRPATH}"/bin:"${PATH}"

# copy application code to WORKDIR
COPY --chown="${OPS_USER}":"${OPS_USER}" . "${APP_HOME}"
COPY ./resources/"${BUILD_ENVIRONMENT}"/start_* "${VENV_DIRPATH}"/bin/
RUN sed -i 's/\r$//g' "${VENV_DIRPATH}"/bin/start_*  \
	&& chmod +x "${VENV_DIRPATH}"/bin/start_* \
	&& chown "${OPS_USER}":"${OPS_USER}" "${APP_HOME}" \
	;

USER "${OPS_USER}"
