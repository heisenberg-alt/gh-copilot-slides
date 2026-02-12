# --- Stage 1: Go CLI build ---
FROM golang:1.23-alpine AS go-builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /slides ./cmd/slides

# --- Stage 2: Python runtime ---
FROM python:3.12-slim AS runtime

# System deps for python-pptx (lxml) and potential PDF export
RUN apt-get update && \
    apt-get install -y --no-install-recommends libxml2 libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install Python package
COPY pyproject.toml README.md ./
COPY slide_mcp/ slide_mcp/
COPY templates/ templates/
RUN pip install --no-cache-dir -e '.[research]'

# Copy Go binary
COPY --from=go-builder /slides /usr/local/bin/slides

# Copy presets (needed by both Go and Python)
COPY templates/presets/ templates/presets/

# Drop to non-root
USER appuser

# Default: run MCP server on stdio
ENTRYPOINT ["python", "-m", "slide_mcp"]
