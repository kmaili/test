import os

DOIT_CONFIG = {"default_tasks": ["local"]}
IMAGE_BASE_URL = "releases.registry.docker.kaisens.fr"
HADOLINT_IMAGE_PATH = "kaisensdata/devops/docker-images/hadolint"
HADOLINT_IMAGE_TAG = "2.7.0-2"
HADOLINT_FULL_IMAGE_PATH = (
    f"{IMAGE_BASE_URL}/{HADOLINT_IMAGE_PATH}:{HADOLINT_IMAGE_TAG}"
)
VENV_NAME = "/home/vagrant/venv"
PYTHON_VERSION = "python3.10"
PYTHON_BIN_FILE = f"/usr/bin/{PYTHON_VERSION}"
SITE_PACKAGES = f"{VENV_NAME}/lib/{PYTHON_VERSION}/site-packages"
REQUIREMENTS_DIR = "requirements"
BIN_DIR = f"{VENV_NAME}/bin"
PIP_CONFIG_FILE="pip.conf"
cwd = os.getcwd()


def task_create_venv():
    """Create python venv"""

    def check_venv_folder_exists():
        venv_parent_dirname = "/".join(VENV_NAME.split("/")[:-1])
        return VENV_NAME.split("/")[-1] in os.listdir(venv_parent_dirname)

    return {
        "actions": [f"virtualenv --python {PYTHON_BIN_FILE} {VENV_NAME}"],
        "targets": [VENV_NAME],
        "verbosity": 2,
        "uptodate": [check_venv_folder_exists],
        "doc": "Create python venv",
    }


def task_lint():
    """Lint Dockerfile"""
    return {
        "actions": [
            f"docker run -it -v {cwd}:/app {HADOLINT_FULL_IMAGE_PATH} hadolint /app/Dockerfile",
        ],
        "file_dep": ["Dockerfile"],
        "verbosity": 2,
        "doc": "Lint Dockerfile",
    }


def task_requirements_local():
    """Generates local requirements"""

    return {
        "actions": [
            f"{BIN_DIR}/pip install pip-tools",
            f"{BIN_DIR}/pip-compile --resolver=backtracking --no-emit-index-url --no-emit-trusted-host --output-file={REQUIREMENTS_DIR}/local {REQUIREMENTS_DIR}/local.in",
        ],
        "task_dep": ["create_venv"],
        "file_dep": [f"{REQUIREMENTS_DIR}/local.in"],
        "targets": [f"{REQUIREMENTS_DIR}/local"],
        "verbosity": 2,
        "doc": "Generates local requirements",
    }


def task_local():
    """Init local env"""
    return {
        "actions": [
            f"{BIN_DIR}/pip install -r {REQUIREMENTS_DIR}/local",
        ],
        "task_dep": ["lint", "requirements_local"],
        "file_dep": [f"{REQUIREMENTS_DIR}/local"],
        "verbosity": 2,
        "doc": "Init local env",
    }


def task_requirements_prod():
    """Generates prod requirements"""

    return {
        "actions": [
            f"{BIN_DIR}/pip install pip-tools",
            f"{BIN_DIR}/pip-compile --resolver=backtracking --no-emit-index-url --no-emit-trusted-host --output-file={REQUIREMENTS_DIR}/prod {REQUIREMENTS_DIR}/prod.in",
        ],
        "task_dep": ["create_venv"],
        "file_dep": [f"{REQUIREMENTS_DIR}/prod.in"],
        "targets": [f"{REQUIREMENTS_DIR}/prod"],
        "verbosity": 2,
        "doc": "Generates prod requirements",
    }


def task_prod():
    """Prepare prod env"""
    prod_mocked_env_vars = {
        "DJANGO_SETTINGS_MODULE": "config.settings.production",
        "DJANGO_ADMIN_URL": "admin/",
        "DJANGO_SECRET_KEY": "rAiOceRzbb6ebsC0rJsxiEQHqbB",
        "SENTRY_DSN": "https://59317663d047410ba1aa07954abf4dff@o548541.ingest.sentry.io/5737539",
        "REDIS_URL": "redis://redis:6379/0",
        "CELERY_BROKER_URL": "redis://redis:6379/0",
        "CELERY_FLOWER_USER": "debug",
        "CELERY_FLOWER_PASSWORD": "debug",
        "DATABASE_URL": "postgresql://debug:debug@postgres:5432/test_db",
        "DJANGO_AWS_ACCESS_KEY_ID": "debug",
        "DJANGO_AWS_SECRET_ACCESS_KEY": "debug",
        "DJANGO_AWS_STORAGE_BUCKET_NAME": "debug",
    }
    docker_env_vars = " ".join(
        [f"-e {key}='{value}'" for key, value in prod_mocked_env_vars.items()]
    )
    return {
        "actions": [
            "docker build -t okk .",
            f"docker run -it {docker_env_vars} -v {cwd}:/app okk python /app/manage.py collectstatic --noinput",
        ],
        "task_dep": ["lint", "requirements_prod"],
        "verbosity": 2,
        "doc": " Prepare prod env ",
    }
