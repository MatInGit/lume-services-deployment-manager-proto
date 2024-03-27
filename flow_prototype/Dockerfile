FROM prefecthq/prefect:2.14.2-python3.11
COPY requirements.txt /opt/prefect/flow_prototype/requirements.txt
RUN python -m pip install -r /opt/prefect/flow_prototype/requirements.txt --no-cache-dir
COPY . /opt/prefect/flow_prototype/
WORKDIR /opt/prefect/flow_prototype/
