# A simple Web UI for my SSID monitor

# Some bits from https://github.com/MegaMosquito/netstuff/blob/master/Makefile
LOCAL_DEFAULT_ROUTE     := $(shell sh -c "ip route | grep default")
LOCAL_ROUTER_ADDRESS    := $(word 3, $(LOCAL_DEFAULT_ROUTE))
LOCAL_IP_ADDRESS        := $(word 7, $(LOCAL_DEFAULT_ROUTE))

# Calculate the SSID name and frequency
SSID_NAME               := $(shell sh -c 'grep "ssid=" /etc/wpa_supplicant/wpa_supplicant.conf | sed "s/.*ssid=.//;s/.$$//g"')
SSID_FREQ               := $(shell sh -c 'echo `hostname` | sed "s/.*-//"')


# ----------------------------------------------------------------------------

IMAGE_NAME := 'ibmosquito/ssidmon:1.0.0'

all: build run

# Build the docker container
build:
	docker build -t $(IMAGE_NAME) -f ./Dockerfile .

# Push the docker container to DockerHub
push:
	docker push $(IMAGE_NAME)

# Remove the local container image
clean:
	-docker rm -f $(IMAGE_NAME) 2>/dev/null || :
	-docker rmi -f $(IMAGE_NAME) 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	-docker rm -f ssid 2>/dev/null || :
	docker run -it -p 0.0.0.0:8000:6006 \
            --name ssid --restart unless-stopped \
            -e SSID_NAME=$(SSID_NAME) \
            -e SSID_FREQ=$(SSID_FREQ) \
            -e LOCAL_ROUTER_ADDRESS=$(LOCAL_ROUTER_ADDRESS) \
            -e LOCAL_IP_ADDRESS=$(LOCAL_IP_ADDRESS) \
            $(IMAGE_NAME) /bin/sh

run:
	-docker rm -f ssid 2>/dev/null || :
	docker run -d -p 0.0.0.0:80:6006 \
            --name ssid --restart unless-stopped \
            -e SSID_NAME=$(SSID_NAME) \
            -e SSID_FREQ=$(SSID_FREQ) \
            -e LOCAL_ROUTER_ADDRESS=$(LOCAL_ROUTER_ADDRESS) \
            -e LOCAL_IP_ADDRESS=$(LOCAL_IP_ADDRESS) \
            $(IMAGE_NAME)

