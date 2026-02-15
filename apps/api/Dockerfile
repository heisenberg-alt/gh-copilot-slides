# Build stage for Go CLI (optional, for combined image)
FROM golang:1.23-alpine AS go-builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/

RUN CGO_ENABLED=0 GOOS=linux go build -o /slides ./cmd/slides


# Python runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Copy Go binary (optional)
COPY --from=go-builder /slides /usr/local/bin/slides

# Copy Python packages
COPY slide_mcp/ ./slide_mcp/
COPY templates/ ./templates/
COPY pyproject.toml ./

# Copy API package
COPY apps/api/ ./apps/api/

# Install Python dependencies
RUN uv pip install --system -e . && \
    uv pip install --system -e ./apps/api

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
