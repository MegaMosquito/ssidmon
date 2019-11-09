FROM arm32v6/python:3-alpine

RUN apk --no-cache --update add curl

# Install flask (for the REST API server)
RUN pip install Flask

# Copy over the source code
COPY ssid.py /
WORKDIR /

# Run the daemon
CMD python ssid.py

