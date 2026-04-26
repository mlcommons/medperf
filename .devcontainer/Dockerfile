FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Remove broken Yarn apt repo to allow docker-in-docker feature to install cleanly
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/trusted.gpg.d/yarn.gpg