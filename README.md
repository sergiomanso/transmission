# Transmission Operator

## Description

Transmission is an open source BitTorrent client, designed for easy and powerful use.
It provides a features like watch directories, bad peer blocklists, and the web interface.

## Quickstart

Assuming you have Juju installed and bootstrapped on a Kubernetes cluster (if you do not, see the
next section):

```bash
# Clone the charm code
$ git clone https://github.com/sergiomanso/transmission && cd transmission

# Build the charm package
$ charmcraft pack

# Deploy the Transmission charm
$ juju deploy ./transmission.charm --resource transmission-image=ghcr.io/linuxserver/transmission --config external-url="transmission.juju"

# Deploy the ingress integrator charm
$ juju deploy nginx-ingress-integrator --config ingress-class="public"

# Relate transmission and ingress integrator
$ juju add-relation transmission nginx-ingress-integrator

# Add an entry to /etc/hosts
$ echo "127.0.1.1 transmission.juju" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

Once the deployment settles, get the password for the admin user
```bash
$ juju run-action --wait transmission get-password
``` 

You can now login to the web GUI which is available at http://transmission.juju

## Development Setup

To set up a local test environment with [MicroK8s](https://microk8s.io):

```bash
# Install MicroK8s
$ sudo snap install --classic microk8s

# Wait for MicroK8s to be ready
$ sudo microk8s status --wait-ready

# Enable features required by Juju controller & charm
$ sudo microk8s enable storage dns ingress

# (Optional) Alias kubectl bundled with MicroK8s package
$ sudo snap alias microk8s.kubectl kubectl

# (Optional) Add current user to 'microk8s' group
# This avoid needing to use 'sudo' with the 'microk8s' command
$ sudo usermod -aG microk8s $(whoami)

# Activate the new group (in the current shell only)
# Log out and log back in to make the change system-wide
$ newgrp microk8s

# Install Charmcraft
$ sudo snap install charmcraft

# Install juju
$ sudo snap install --classic juju

# Bootstrap the Juju controller on MicroK8s
$ juju bootstrap microk8s micro

# Add a new model to Juju
$ juju add-model development
```

## Build and Deploy Locally

```bash
# Clone the charm code
$ git clone https://github.com/sergiomanso/transmission && cd transmission

# Build the charm package
$ charmcraft pack

# Deploy the Transmission charm
$ juju deploy ./transmission.charm --resource transmission-image=ghcr.io/linuxserver/transmission --config external-url="transmission.juju"

# Deploy the ingress integrator charm
$ juju deploy nginx-ingress-integrator --config ingress-class="public"

# Relate transmission and ingress integrator
$ juju add-relation transmission nginx-ingress-integrator

# Add an entry to /etc/hosts
$ echo "127.0.1.1 transmission.juju" | sudo tee -a /etc/hosts

# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

Once the deployment settles, get the password for the admin user
```bash
$ juju run-action --wait transmission get-password
``` 

You can now login to the web GUI which is available at http://transmission.juju


## Testing

```bash
# Clone the charm code
$ git clone https://github.com/sergiomanso/transmission && cd transmission

# Install python3-virtualenv
$ sudo apt update && sudo apt install -y python3-virtualenv

# Create a virtualenv for the charm code
$ virtualenv venv

# Activate the venv
$ source ./venv/bin/activate

# Install dependencies
$ pip install -r requirements-dev.txt

# Run the tests
$ ./run_tests
```

## TODO/Roadmap

* establish a certificates relation (eg easyrsa)
* add missing config validation

