FROM python:3.11-slim

LABEL maintainer="nat@a-cyborg.com"

WORKDIR /home

COPY requirements.txt .
RUN python3.11 -m venv /home/venv && \
    /home/venv/bin/python -m pip install --upgrade pip && \
    /home/venv/bin/python -m pip install -r /home/requirements.txt

COPY run.sh .
COPY octahedroflake.py .
COPY mesh_generator.py .

RUN chmod +x run.sh

CMD ["/home/run.sh", "--no-prompt"]
