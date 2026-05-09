FROM python:3.12-slim

WORKDIR /app

# Install breadcrumb-cli from PyPI
RUN pip install breadcrumb-cli

# Mount the repo as a volume
VOLUME ["/repo"]
WORKDIR /repo

# Set entrypoint to breadcrumb
ENTRYPOINT ["breadcrumb"]
CMD ["--help"]
