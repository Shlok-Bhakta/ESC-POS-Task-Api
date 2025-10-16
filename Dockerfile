FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen

COPY main.py ./

ENV PRINTER_DEVICE=/dev/usb/lp0

EXPOSE 5000

CMD ["uv", "run", "python", "main.py"]
