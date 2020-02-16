FROM arm32v6/python:3-alpine

# Install build tools
RUN apk --no-cache --update add curl jq gawk bc socat git gcc libc-dev linux-headers scons swig

# Install the python GPIO library
RUN pip install RPi.GPIO

# Install flask (for the REST API server)
RUN pip install Flask

# Copy over the source code
COPY ssid.py /
WORKDIR /

# Run the daemon
CMD python ssid.py

