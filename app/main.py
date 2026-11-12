"""SBDT UTS: API inference dengan SSO JWT dan routing primary/replica."""
import os
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import joblib
import jwt
import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from jwt import PyJWKClient, PyJWTError
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

app = FastAPI(title="SBDT Distributed Inference API", version="1.0.0")

DB_USER = os.getenv("DB_USER", "sbdt")
DB_PASSWORD = os.getenv("DB_PASSWORD", "sbdt_demo_password")
DB_NAME = os.getenv("DB_NAME", "sbdt")
PRIMARY_HOST = os.getenv("DB_PRIMARY_HOST", "postgres-primary")
REPLICA_HOST = os.getenv("DB_REPLICA_HOST", "postgres-replica")
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:8080/realms/sbdt")
OIDC_JWKS_URL = os.getenv(
    "OIDC_JWKS_URL", "http://keycloak:8080/realms/sbdt/protocol/openid-connect/certs"
)
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "api-service")
MODEL_PATH = os.getenv("MODEL_PATH", "models/risk_model.joblib")


class InferenceRequest(BaseModel):
    transaction_amount: float = Field(gt=0, le=1_000_000_000)
    transactions_24h: int = Field(ge=0, le=10_000)
    new_device: bool


@lru_cache

def get_jwks_client():
    return PyJWKClient(OIDC_JWKS_URL, lifespan=300)


@lru_cache

def get_model():
    path = Path(MODEL_PATH)
    if not path.is_file():
        raise RuntimeError("Model belum tersedia. Jalankan app/train_model.py.")
    return joblib.load(path)  # Hanya load artefak model lokal yang tepercaya.


def verify_token(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token wajib disertakan")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
            leeway=10,
        )
        return claims
    except (PyJWTError, ValueError, OSError) as exc:
        raise HTTPException(status_code=401, detail="Token tidak valid") from exc


@contextmanager
def connection(host):
    with psycopg.connect(
        host=host,
        port=5432,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        connect_timeout=5,
        row_factory=dict_row,
    ) as conn:
        yield conn


@app.get("/health")
def health():
    return {"status": "ok", "service": "sbdt-api"}


@app.get("/health/database")
def database_health(claims: dict = Depends(verify_token)):
    status = {}
    for role, host in (("primary", PRIMARY_HOST), ("replica", REPLICA_HOST)):
        try:
            with connection(host) as conn:
                row = conn.execute("SELECT pg_is_in_recovery() AS is_replica").fetchone()
            status[role] = {"reachable": True, "is_replica": row["is_replica"]}
        except psycopg.Error:
            status[role] = {"reachable": False}
    return status


@app.post("/predict", status_code=201)
def predict(payload: InferenceRequest, response: Response, claims: dict = Depends(verify_token)):
    model = get_model()
    features = [[payload.transaction_amount, payload.transactions_24h, int(payload.new_device)]]
    probability = float(model.predict_proba(features)[0][1])
    label = "tinggi" if probability >= 0.5 else "rendah"
    try:
        with connection(PRIMARY_HOST) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO inference_history
                       (username, transaction_amount, transactions_24h,
                        new_device, risk_probability, risk_label)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, created_at""",
                    (claims.get("preferred_username", claims["sub"]),
                     payload.transaction_amount, payload.transactions_24h,
                     payload.new_device, probability, label),
                )
                stored = cur.fetchone()
            conn.commit()
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Primary DB belum siap") from exc
    response.headers["X-Write-Node"] = "postgres-primary"
    return {"id": stored["id"], "risk_label": label,
            "risk_probability": round(probability, 4),
            "created_at": stored["created_at"], "stored_at": "primary"}


@app.get("/inferences")
def history(response: Response, claims: dict = Depends(verify_token)):
    try:
        with connection(REPLICA_HOST) as conn:
            rows = conn.execute(
                """SELECT id, username, transaction_amount, transactions_24h,
                          new_device, risk_probability, risk_label, created_at
                   FROM inference_history WHERE username = %s
                   ORDER BY id DESC LIMIT 30""",
                (claims.get("preferred_username", claims["sub"]),),
            ).fetchall()
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Read replica belum siap") from exc
    response.headers["X-Read-Node"] = "postgres-replica"
    return {"source": "read-replica", "data": rows,
            "note": "Replikasi asynchronous: data baru mungkin muncul dengan sedikit jeda."}
