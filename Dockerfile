FROM cadquery/cadquery:latest
USER root

LABEL maintainer="nat@a-cyborg.com"

RUN apt-get update
RUN apt-get install bc
RUN apt-get clean && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /home

COPY run.sh .
COPY logo_stamp.step .
COPY octahedroflake.py .

RUN chmod +x run.sh
CMD ["/home/run.sh"]