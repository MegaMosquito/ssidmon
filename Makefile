# A simple Web UI for my SSID monitor

# Some bits from https://github.com/MegaMosquito/netstuff/blob/master/Makefile
LOCAL_DEFAULT_ROUTE     := $(shell sh -c "ip route | grep default")
LOCAL_ROUTER_ADDRESS    := $(word 3, $(LOCAL_DEFAULT_ROUTE))
LOCAL_IP_ADDRESS        := $(word 7, $(LOCAL_DEFAULT_ROUTE))

# Calculate the SSID name and frequency
SSID_NAME               := $(shell sh -c 'grep "ssid=" /etc/wpa_supplicant/wpa_supplicant.conf | sed "s/.*ssid=.//;s/.$$//g"')
SSID_FREQ               := $(shell sh -c 'echo `hostname` | sed "s/.*-//"')


# ----------------------------------------------------------------------------

all: build run

# Build the docker container
build:
	docker build -t ssid -f ./Dockerfile .

# Remove the local container image
clean:
	-docker rm -f ssid 2>/dev/null || :
	-docker rmi -f ssid 2>/dev/null || :

# ----------------------------------------------------------------------------

dev:
	-docker rm -f ssid 2>/dev/null || :
	docker run -it -p 0.0.0.0:8000:6006 \
            --name ssid --restart unless-stopped \
            -e SSID_NAME=$(SSID_NAME) \
            -e SSID_FREQ=$(SSID_FREQ) \
            -e LOCAL_ROUTER_ADDRESS=$(LOCAL_ROUTER_ADDRESS) \
            -e LOCAL_IP_ADDRESS=$(LOCAL_IP_ADDRESS) \
            ssid /bin/sh

run:
	-docker rm -f ssid 2>/dev/null || :
	docker run -d -p 0.0.0.0:80:6006 \
            --name ssid --restart unless-stopped \
            -e SSID_NAME=$(SSID_NAME) \
            -e SSID_FREQ=$(SSID_FREQ) \
            -e LOCAL_ROUTER_ADDRESS=$(LOCAL_ROUTER_ADDRESS) \
            -e LOCAL_IP_ADDRESS=$(LOCAL_IP_ADDRESS) \
            ssid

