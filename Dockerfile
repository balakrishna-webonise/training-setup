# FROM python:3.11-slim

# # Install system deps
# RUN apt-get update && apt-get install -y git curl build-essential libpq-dev

# # Install DBT and Postgres adapter
# RUN pip install --no-cache-dir dbt-postgres

# # Create workspace
# WORKDIR /usr/app
# COPY . .

# CMD ["bash"]

# Use official Python slim base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DBT_PROFILES_DIR=/usr/app/.dbt

ARG UID=1001
ARG GID=1001

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN useradd -ms /bin/bash dbtuser

# Switch to the new user home directory
WORKDIR /usr/app

# Copy project files and fix permissions
COPY --chown=dbtuser:dbtuser . .

# Install DBT and Postgres adapter
RUN pip install dbt-postgres

# Switch to non-root user
USER dbtuser

# Default command
CMD ["bash"]
