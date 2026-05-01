FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY promptgate ./promptgate
COPY policies ./policies
RUN pip install --no-cache-dir -e .
EXPOSE 8787
CMD ["uvicorn", "promptgate.server:app", "--host", "0.0.0.0", "--port", "8787"]
