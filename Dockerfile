FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
COPY app/train_model.py ./app/train_model.py
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
    && python app/train_model.py

FROM python:3.11-slim AS runtime
WORKDIR /srv
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels \
    && useradd --system --create-home --uid 10001 appuser
COPY app/ ./app/
COPY --from=builder /build/models ./models
ENV PYTHONUNBUFFERED=1 MODEL_PATH=/srv/models/risk_model.joblib
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
