FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONSAFEPATH=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY vaaniseva_rt ./vaaniseva_rt
RUN mkdir -p /app/data && useradd --create-home --uid 10001 vaaniseva \
    && chown -R vaaniseva:vaaniseva /app/data \
    && chmod -R a+rX /app/vaaniseva_rt/assets

USER vaaniseva
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/health', timeout=3)"

CMD ["python", "-P", "-m", "uvicorn", "vaaniseva_rt.server:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers", "--forwarded-allow-ips", "*"]
