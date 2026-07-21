"""FastAPI staging service for the already-frozen uplift policy artifact."""

from __future__ import annotations

import argparse
import os
import secrets
import time
import uuid
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from causal_uplift_experimentation_ops.api.errors import (
    ArtifactLoadError,
    AuthenticationError,
    GuardrailValidationError,
    PolicyScoringError,
    PolicyServiceInputError,
)
from causal_uplift_experimentation_ops.api.safety import (
    JSONLAuditLogger,
    OperationalMetrics,
    StagingAPIConfig,
)
from causal_uplift_experimentation_ops.api.schemas import (
    BatchScoreRequest,
    BatchScoreResponse,
    HealthResponse,
    ManifestResponse,
    MetricsResponse,
    PolicyResponse,
    ScoreResponse,
    UserFeatures,
    VersionResponse,
)
from causal_uplift_experimentation_ops.api.service import (
    DEFAULT_ARTIFACT_PATH,
    PolicyInferenceService,
)
from causal_uplift_experimentation_ops.artifacts.manifest import package_version

PROTECTED_ENDPOINTS = {"/score", "/score-batch", "/manifest", "/policy"}
AUDITED_ENDPOINTS = {"/score", "/score-batch"}


def create_app(
    artifact_path: Path | str = DEFAULT_ARTIFACT_PATH,
    max_batch_size: int | None = None,
    safety_config: StagingAPIConfig | None = None,
) -> FastAPI:
    """Create a staging API with configurable local safety controls."""
    settings = safety_config or StagingAPIConfig.from_environment()
    if max_batch_size is not None:
        settings = replace(settings, max_batch_size=max_batch_size)
    application = FastAPI(
        title="Causal Uplift Policy Staging API",
        version=package_version(),
        description=(
            "Local/staging inference for a frozen synthetic uplift policy artifact. "
            "This service does not train models or authorize production treatment."
        ),
    )
    try:
        service: PolicyInferenceService | None = PolicyInferenceService(
            artifact_path,
            safety_config=settings,
        )
        load_error: str | None = None
    except ArtifactLoadError as error:
        service = None
        load_error = str(error)
    application.state.policy_service = service
    application.state.artifact_load_error = load_error
    application.state.safety_config = settings
    application.state.audit_logger = JSONLAuditLogger(
        settings.enable_audit_log,
        settings.audit_log_path,
    )
    application.state.operational_metrics = OperationalMetrics()

    def request_id(request: Request) -> str:
        return str(request.state.request_id)

    def loaded_service() -> PolicyInferenceService:
        current = application.state.policy_service
        if current is None:
            raise ArtifactLoadError(application.state.artifact_load_error)
        return current

    def authenticate(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> None:
        if not settings.require_api_key:
            return
        expected = os.getenv(settings.api_key_env_var)
        if not expected:
            request.state.error_type = "authentication_not_configured"
            raise AuthenticationError(
                f"API key environment variable {settings.api_key_env_var!r} is not configured"
            )
        if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
            request.state.error_type = "authentication_failed"
            raise AuthenticationError("Missing or invalid API key")

    def error_response(
        request: Request,
        *,
        status_code: int,
        detail: object,
        error_type: str,
    ) -> JSONResponse:
        request.state.error_type = error_type
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": jsonable_encoder(detail),
                "request_id": request_id(request),
                "error_type": error_type,
            },
        )

    @application.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request,
        error: AuthenticationError,
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=401,
            detail=str(error),
            error_type="authentication_error",
        )

    @application.exception_handler(ArtifactLoadError)
    async def artifact_error_handler(
        request: Request,
        error: ArtifactLoadError,
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=503,
            detail=str(error),
            error_type="artifact_load_error",
        )

    @application.exception_handler(GuardrailValidationError)
    async def guardrail_error_handler(
        request: Request,
        error: GuardrailValidationError,
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=400,
            detail=str(error),
            error_type="guardrail_validation_error",
        )

    @application.exception_handler(PolicyServiceInputError)
    async def input_error_handler(
        request: Request,
        error: PolicyServiceInputError,
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=400,
            detail=str(error),
            error_type="request_validation_error",
        )

    @application.exception_handler(PolicyScoringError)
    async def scoring_error_handler(
        request: Request,
        error: PolicyScoringError,
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=500,
            detail=str(error),
            error_type="scoring_error",
        )

    @application.exception_handler(RequestValidationError)
    async def pydantic_error_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=422,
            detail=error.errors(),
            error_type="payload_validation_error",
        )

    @application.middleware("http")
    async def request_operations(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - started) * 1_000
        response.headers["X-Request-ID"] = request_id(request)

        if request.url.path in AUDITED_ENDPOINTS:
            context = getattr(request.state, "operation_context", {})
            current = application.state.policy_service
            is_error = response.status_code >= 400
            endpoint = request.url.path
            users_scored = int(context.get("users_scored", 0))
            recommendations = int(context.get("recommendations", 0))
            application.state.operational_metrics.record(
                endpoint=endpoint,
                users_scored=users_scored,
                recommendations=recommendations,
                latency_ms=latency_ms,
                is_error=is_error,
            )
            application.state.audit_logger.write(
                {
                    "endpoint": endpoint,
                    "request_id": request_id(request),
                    "batch_size": int(context.get("batch_size", 0)),
                    "artifact_version": context.get(
                        "artifact_version",
                        current.config.artifact_version if current else None,
                    ),
                    "model_name": context.get(
                        "model_name",
                        current.config.model_name if current else None,
                    ),
                    "policy_name": context.get(
                        "policy_name",
                        current.config.policy_name if current else None,
                    ),
                    "recommended_treatment_count": recommendations,
                    "mean_predicted_uplift": context.get("mean_predicted_uplift"),
                    "min_predicted_uplift": context.get("min_predicted_uplift"),
                    "max_predicted_uplift": context.get("max_predicted_uplift"),
                    "status": "error" if is_error else "success",
                    "error_type": getattr(request.state, "error_type", None),
                    "latency_ms": latency_ms,
                }
            )
        return response

    def set_success_context(
        request: Request,
        scores: list[ScoreResponse],
    ) -> None:
        uplifts = [score.predicted_uplift for score in scores]
        current = loaded_service()
        request.state.operation_context = {
            "batch_size": len(scores),
            "users_scored": len(scores),
            "recommendations": sum(
                score.recommended_treatment for score in scores
            ),
            "artifact_version": current.config.artifact_version,
            "model_name": current.config.model_name,
            "policy_name": current.config.policy_name,
            "mean_predicted_uplift": sum(uplifts) / len(uplifts),
            "min_predicted_uplift": min(uplifts),
            "max_predicted_uplift": max(uplifts),
        }

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        current = application.state.policy_service
        if current is None:
            return HealthResponse(
                status="degraded",
                artifact_loaded=False,
                service="causal-uplift-policy-staging",
                detail=application.state.artifact_load_error,
            )
        return HealthResponse(
            status="ok",
            artifact_loaded=True,
            service="causal-uplift-policy-staging",
            artifact_version=current.config.artifact_version,
            model_name=current.config.model_name,
            policy_name=current.config.policy_name,
        )

    @application.get("/version", response_model=VersionResponse)
    def version() -> VersionResponse:
        return loaded_service().version

    @application.get(
        "/policy",
        response_model=PolicyResponse,
        dependencies=[Depends(authenticate)],
    )
    def policy() -> PolicyResponse:
        return loaded_service().policy_summary

    @application.post(
        "/score",
        response_model=ScoreResponse,
        dependencies=[Depends(authenticate)],
    )
    def score(request: Request, user: UserFeatures) -> ScoreResponse:
        result = loaded_service().score_user(
            user,
            request_id=request_id(request),
        )
        set_success_context(request, [result])
        return result

    @application.post(
        "/score-batch",
        response_model=BatchScoreResponse,
        dependencies=[Depends(authenticate)],
    )
    def score_batch(
        request: Request,
        batch: BatchScoreRequest,
    ) -> BatchScoreResponse:
        result = loaded_service().score_batch(
            batch.users,
            request_id=request_id(request),
            max_recommendations=batch.max_recommendations,
            max_treatment_cost=batch.max_treatment_cost,
            treatment_cost_per_user=batch.treatment_cost_per_user,
        )
        set_success_context(request, result.scores)
        return result

    @application.get(
        "/manifest",
        response_model=ManifestResponse,
        dependencies=[Depends(authenticate)],
    )
    def manifest() -> ManifestResponse:
        return loaded_service().manifest_summary

    @application.get("/metrics", response_model=MetricsResponse)
    def metrics() -> MetricsResponse:
        current = loaded_service()
        values = application.state.operational_metrics.snapshot(
            artifact_version=current.config.artifact_version,
            model_name=current.config.model_name,
            policy_name=current.config.policy_name,
        )
        return MetricsResponse(**values)

    return application


app = create_app()


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-batch-size", type=int)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Run the staging API with environment-loaded safety controls."""
    options = _parse_args(args)
    settings = StagingAPIConfig.from_environment()
    if options.max_batch_size is not None:
        settings = replace(settings, max_batch_size=options.max_batch_size)
    try:
        PolicyInferenceService(options.bundle, safety_config=settings)
    except ArtifactLoadError as error:
        raise SystemExit(f"Cannot start policy API: {error}") from error
    uvicorn.run(
        create_app(options.bundle, safety_config=settings),
        host=options.host,
        port=options.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Temporary PatchProof policy test.
