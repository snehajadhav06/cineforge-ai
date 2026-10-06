from fastapi import APIRouter
from backend.schemas import HardwareInfo
from backend.services.system_service import system_service

router = APIRouter(prefix="/api/system", tags=["System Hardware"])


@router.get("", response_model=HardwareInfo)
def get_system_hardware():
    return system_service.get_hardware_info()
