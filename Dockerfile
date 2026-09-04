FROM python:3.14-slim

WORKDIR /app

# Useful defaults for Python inside containers.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv inside the image.
RUN pip install --no-cache-dir uv

# Copy dependency files first so Docker can cache this layer.
COPY pyproject.toml uv.lock ./

# Install locked dependencies without installing the app as a Python package.
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application code.
COPY . .

# Use the virtual environment created by uv.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# 0.0.0.0 is required so FastAPI is reachable outside the container.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]