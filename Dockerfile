FROM python:3.13-alpine AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

FROM base AS builder

RUN apk add --no-cache gcc musl-dev bash

RUN python -m venv /venv

COPY . .

RUN uv sync --locked --all-groups

# Install grpcio-tools explicitly if not already installed
RUN /venv/bin/pip install grpcio-tools>=1.76.0

# Run proto compilation with the venv Python directly
RUN /venv/bin/python -m grpc_tools.protoc \
    -I proto/ \
    --python_out=. \
    --grpc_python_out=. \
    --pyi_out=. \
    $(find proto -name "*.proto" -type f)

# Verify proto files were generated
RUN ls -la bambu_spoolman/grpc/*_pb2*.py

RUN uv build && /venv/bin/pip install dist/*.whl

# Verify proto files are in the installed package
RUN ls -la /venv/lib/python3.13/site-packages/bambu_spoolman/grpc/*_pb2*.py || echo "Proto files not in wheel, copying manually..."

# Copy generated proto files to venv
RUN cp bambu_spoolman/grpc/*_pb2*.py /venv/lib/python3.13/site-packages/bambu_spoolman/grpc/


FROM node:23-alpine AS frontend_builder

RUN apk add --no-cache protobuf protobuf-dev tree

WORKDIR /app

COPY frontend /app/frontend

RUN corepack enable pnpm && cd /app/frontend && pnpm install --ignore-scripts
COPY proto /app/proto


RUN cd /app/frontend && pnpm proto-generate && pnpm build

FROM base AS app

RUN apk add --no-cache supervisor nodejs pnpm

ENV LOGURU_LEVEL=INFO

COPY --from=builder /venv /venv
COPY --from=builder /app/bambu_spoolman /app/bambu_spoolman
COPY --from=frontend_builder /app/frontend/public /app/frontend/public
COPY --from=frontend_builder /app/frontend/.next/standalone /app/frontend
COPY --from=frontend_builder /app/frontend/.next/static /app/frontend/.next/static

COPY conf/supervisord.conf /app/supervisord.conf

CMD ["supervisord", "-c", "/app/supervisord.conf"]
