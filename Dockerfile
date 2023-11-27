FROM continuumio/miniconda3
RUN apt-get update -y && \
	apt install -y libgl1-mesa-glx && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN conda install -c conda-forge -c cadquery cadquery=master && \
	conda clean -a -y
WORKDIR /cadquery

# Copy the script and the Python file into the image
COPY run.sh /home/cq/run.sh
COPY octahedroflake.py /home/cq/octahedroflake.py

# Set execute permissions on the script
RUN chmod +x /home/cq/run.sh

# Switch back to the cq user
USER cq

# Keep the container running with a simple command like tailing a log file
CMD ["tail", "-f", "/dev/null"]
