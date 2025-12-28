"""
Health Router
Handles health check endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide

from app.src.presentation.controllers.health_controller import HealthController
from app.src.application.dto.health_dto import HealthCheckResponseDTO
from app.src.bootstrap.container import Container


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", response_model=HealthCheckResponseDTO)
@inject
async def health_check(
    controller: HealthController = Depends(Provide[Container.health_controller]),
) -> HealthCheckResponseDTO:
    """Full health check - checks all services: Triton, Milvus, Redis, PostgreSQL"""
    try:
        health = await controller.health_check()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ready")
@inject
async def readiness_check(
    controller: HealthController = Depends(Provide[Container.health_controller]),
):
    """Readiness check - returns 200 if service is ready to accept requests"""
    try:
        readiness = await controller.readiness_check()
        if not readiness["ready"]:
            raise HTTPException(
                status_code=503,
                detail="Service not ready"
            )
        return readiness
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live")
@inject
async def liveness_check(
    controller: HealthController = Depends(Provide[Container.health_controller]),
):
    """Liveness check - returns 200 if service is alive"""
    try:
        liveness = await controller.liveness_check()
        return liveness
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
