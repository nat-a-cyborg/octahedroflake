FROM cadquery/cadquery:latest
USER root

LABEL maintainer="nat@a-cyborg.com"

WORKDIR /home

COPY run.sh .
COPY logo_stamp.step .
COPY octahedroflake.py .

RUN chmod +x run.sh
CMD ["/home/run.sh"]
