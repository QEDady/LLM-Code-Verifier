#!/usr/bin/env bash
set -e

######################### Preparing the host environment #########################
# Git
install_git_ubuntu() {
    sudo apt-get update
    sudo apt-get install -y git
}

install_git_centos() {
    sudo yum install -y git
}

# Docker
install_docker_ubuntu() {
  # FROM https://docs.docker.com/engine/install/ubuntu/
  # Add Docker's official GPG key:
  sudo apt-get update
  sudo apt-get install ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc

  # Add the repository to Apt sources:
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update

  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

  # Check if Docker is running. If not, start it.
  if ! sudo systemctl is-active --quiet docker; then
    sudo systemctl start docker
    sudo systemctl enable docker
  fi

  # Check if docker group exists, if not, create it.
  if ! getent group docker &>/dev/null; then
    sudo groupadd docker
  fi

  # Check if the current user is in the docker group. If not, add it.
  if ! groups $USER | grep &>/dev/null '\bdocker\b'; then
    sudo usermod -aG docker $USER
    newgrp docker
  fi
  
  # Print Docker version to verify installation
  docker --version

  echo "Docker installation completed successfully."
}

install_docker_centos() {
    sudo yum install -y yum-utils
    sudo yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo

    sudo yum install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl start docker
    sudo systemctl enable docker
}

if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
        ubuntu|debian)
            if command -v docker &> /dev/null; then
              echo "Docker is already installed."
            else
              install_docker_ubuntu

              # Add the current user to the docker group
              sudo usermod -aG docker $USER

              # Print Docker version to verify installation
              docker --version

              echo "Docker installation completed successfully."
            fi

            if command -v git &> /dev/null; then
              echo "Git is already installed."
            else
              install_git_ubuntu
              echo "Git installation completed successfully."
            fi
            ;;
        centos|rhel|rocky)
            if command -v docker &> /dev/null; then
              echo "Docker is already installed."
            else
              install_docker_centos

              # Add the current user to the docker group
              sudo usermod -aG docker $USER

              # Print Docker version to verify installation
              docker --version

              echo "Docker installation completed successfully."
            fi

            if command -v git &> /dev/null; then
              echo "Git is already installed."
            else
              install_git_centos
              echo "Git installation completed successfully."
            fi
            ;;
        *)
            echo "Unsupported Linux distribution: $ID"
            exit 1
            ;;
    esac
else
    echo "Cannot detect the Linux distribution."
    exit 1
fi

# Docker Compose

######################### Preparing the dev environment #########################
set -x

# Get the user and group names and IDs
echo "USER_NAME=$USER" > .devcontainer/.env
echo "USER_ID=$(id -u)" >> .devcontainer/.env

echo "GROUP_NAME=$GROUP" >> .devcontainer/.env
echo "GROUP_ID=$(id -g)" >> .devcontainer/.env

# Get the git local user name and email
# If not set, get the global user name and email
GIT_USERNAME=$(git config --local user.name)
if [ -z "$GIT_USERNAME" ]; then
  GIT_USERNAME=$(git config --global user.name)
fi
echo "GIT_USERNAME='$GIT_USERNAME'" >> .devcontainer/.env

GIT_EMAIL=$(git config --local user.email)
if [ -z "$GIT_EMAIL" ]; then
  GIT_EMAIL=$(git config --global user.email)
fi
echo "GIT_EMAIL='$GIT_EMAIL'" >> .devcontainer/.env