# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final Image
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user first
RUN useradd -m appuser

# Copy installed packages from builder to appuser's home
COPY --from=builder /root/.local /home/appuser/.local

# Set PATH for appuser
ENV PATH="/home/appuser/.local/bin:$PATH"

# Copy source code
COPY . .

# Copy entrypoint and ensure it's executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

ENTRYPOINT ["./entrypoint.sh"]
CMD ["--help"]

