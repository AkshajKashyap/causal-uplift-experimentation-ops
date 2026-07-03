"""FastAPI staging service for the already-frozen uplift policy artifact."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from causal_uplift_experimentation_ops.api.errors import (
    ArtifactLoadError,
    PolicyServiceInputError,
)
from causal_uplift_experimentation_ops.api.schemas import (
    BatchScoreRequest,
    BatchScoreResponse,
    HealthResponse,
    ManifestResponse,
    PolicyResponse,
    ScoreResponse,
    UserFeatures,
    VersionResponse,
)
from causal_uplift_experimentation_ops.api.service import (
    DEFAULT_ARTIFACT_PATH,
    PolicyInferenceService,
)


def create_app(
    artifact_path: Path | str = DEFAULT_ARTIFACT_PATH,
    max_batch_size: int = 1_000,
) -> FastAPI:
    """Create an API that reports degraded health if its artifact is unavailable."""
    application = FastAPI(
        title="Causal Uplift Policy Staging API",
        version="0.1.0",
        description=(
            "Local/staging inference for a frozen synthetic uplift policy artifact. "
            "This service does not train models or authorize production treatment."
        ),
    )
    try:
        service: PolicyInferenceService | None = PolicyInferenceService(
            artifact_path,
            max_batch_size=max_batch_size,
        )
        load_error: str | None = None
    except ArtifactLoadError as error:
        service = None
        load_error = str(error)
    application.state.policy_service = service
    application.state.artifact_load_error = load_error

    def loaded_service() -> PolicyInferenceService:
        current = application.state.policy_service
        if current is None:
            raise ArtifactLoadError(application.state.artifact_load_error)
        return current

    @application.exception_handler(ArtifactLoadError)
    async def artifact_error_handler(
        _request: Request,
        error: ArtifactLoadError,
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(error)})

    @application.exception_handler(PolicyServiceInputError)
    async def input_error_handler(
        _request: Request,
        error: PolicyServiceInputError,
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(error)})

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

    @application.get("/policy", response_model=PolicyResponse)
    def policy() -> PolicyResponse:
        return loaded_service().policy_summary

    @application.post("/score", response_model=ScoreResponse)
    def score(user: UserFeatures) -> ScoreResponse:
        return loaded_service().score_user(user)

    @application.post("/score-batch", response_model=BatchScoreResponse)
    def score_batch(request: BatchScoreRequest) -> BatchScoreResponse:
        scores = loaded_service().score_users(request.users)
        return BatchScoreResponse(batch_size=len(scores), scores=scores)

    @application.get("/manifest", response_model=ManifestResponse)
    def manifest() -> ManifestResponse:
        return loaded_service().manifest_summary

    return application


app = create_app()


def _parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-batch-size", type=int, default=1_000)
    return parser.parse_args(args)


def main(args: Sequence[str] | None = None) -> int:
    """Run the staging API with a preflight artifact validation."""
    options = _parse_args(args)
    try:
        PolicyInferenceService(
            options.bundle,
            max_batch_size=options.max_batch_size,
        )
    except ArtifactLoadError as error:
        raise SystemExit(f"Cannot start policy API: {error}") from error
    uvicorn.run(
        create_app(options.bundle, max_batch_size=options.max_batch_size),
        host=options.host,
        port=options.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
