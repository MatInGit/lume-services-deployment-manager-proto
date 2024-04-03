FROM python:3.11.8-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends git iputils-ping curl
COPY requirements.txt /opt/prefect/flow_prototype/requirements.txt
RUN python -m pip install botorch tensorflow --no-cache-dir
# the 2 above are heavy dependencies, so we install them first in a separate layer
RUN python -m pip install -r /opt/prefect/flow_prototype/requirements.txt --no-cache-dir
COPY . /opt/deployment/
WORKDIR /opt/deployment/

# install requirements from requirements_model and start main.py
CMD ["python", "entrypoint.py"]