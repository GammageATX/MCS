"""Equipment control endpoints."""

from typing import Literal
from fastapi import APIRouter, Request, status, Path, Depends
from loguru import logger

from mcs.utils.errors import create_error
from mcs.api.communication.services.equipment import EquipmentService
from mcs.api.communication.models.state import (
    EquipmentState,
    FeederState,
    DeagglomeratorState
)
from mcs.api.communication.models.equipment import (
    GasFlowRequest,
    GasValveRequest,
    VacuumPumpRequest,
    GateValveRequest,
    ShutterRequest,
    FeederRequest,
    DeagglomeratorRequest,
    FeederStateRequest,
    NozzleSelectRequest
)


router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("/state", response_model=EquipmentState)
async def get_state(request: Request) -> EquipmentState:
    """Get current equipment state."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        state = await service.equipment.get_equipment_state()
        return state

    except Exception as e:
        error_msg = "Failed to get equipment state"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_msg
        )


@router.get("/internal_states/{state_name}", response_model=bool)
async def get_equipment_internal_state(request: Request, state_name: str) -> bool:
    """Get single equipment-related internal state."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        state = await service.internal_state.get_equipment_state(state_name)
        if state is None:
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"State '{state_name}' not found"
            )
            
        return state

    except Exception as e:
        error_msg = f"Failed to get equipment internal state {state_name}"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_msg
        )


@router.get("/feeders/{feeder_id}", response_model=FeederState)
async def get_feeder_state(
    feeder_id: int = Path(..., description="ID of feeder to get state for (1 or 2)"),
    equipment_service: EquipmentService = Depends()
) -> FeederState:
    """Get state of specific feeder."""
    return await equipment_service.get_feeder_state(feeder_id)


@router.get("/deagglomerators/{deagg_id}", response_model=DeagglomeratorState)
async def get_deagglomerator_state(
    deagg_id: int = Path(..., description="ID of deagglomerator to get state for (1 or 2)"),
    equipment_service: EquipmentService = Depends()
) -> DeagglomeratorState:
    """Get state of specific deagglomerator."""
    return await equipment_service.get_deagglomerator_state(deagg_id)


@router.get("/gas/main/flow")
async def get_main_flow(request: Request):
    """Get main gas flow state."""
    try:
        gas_state = await request.app.state.service.equipment.get_gas_state()
        return {
            "setpoint": gas_state.main_flow_setpoint,
            "actual": gas_state.main_flow_actual
        }
    except Exception as e:
        logger.error(f"Failed to get main flow: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get main flow: {str(e)}"
        )


@router.get("/gas/feeder/flow")
async def get_feeder_flow(request: Request):
    """Get feeder gas flow state."""
    try:
        gas_state = await request.app.state.service.equipment.get_gas_state()
        return {
            "setpoint": gas_state.feeder_flow_setpoint,
            "actual": gas_state.feeder_flow_actual
        }
    except Exception as e:
        logger.error(f"Failed to get feeder flow: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get feeder flow: {str(e)}"
        )


@router.put("/gas/main/flow")
async def set_main_gas_flow(request: Request, flow: GasFlowRequest):
    """Set main gas flow."""
    try:
        await request.app.state.service.equipment.set_main_gas_flow(flow.flow)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set main gas flow: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set main gas flow: {str(e)}"
        )


@router.put("/gas/feeder/flow")
async def set_feeder_gas_flow(request: Request, flow: GasFlowRequest):
    """Set feeder gas flow."""
    try:
        await request.app.state.service.equipment.set_feeder_gas_flow(flow.flow)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder gas flow: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder gas flow: {str(e)}"
        )


@router.put("/gas/main/valve")
async def set_main_gas_valve(request: Request, valve: GasValveRequest):
    """Set main gas valve state."""
    try:
        await request.app.state.service.equipment.set_main_gas_valve(valve.open)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set main gas valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set main gas valve: {str(e)}"
        )


@router.put("/gas/feeder/valve")
async def set_feeder_gas_valve(request: Request, valve: GasValveRequest):
    """Set feeder gas valve state."""
    try:
        await request.app.state.service.equipment.set_feeder_gas_valve(valve.open)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder gas valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder gas valve: {str(e)}"
        )


@router.put("/vacuum/gate_valve")
async def set_gate_valve(request: Request, valve: GateValveRequest):
    """Set gate valve state."""
    try:
        await request.app.state.service.equipment.set_gate_valve(valve.open, valve.partial)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set gate valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set gate valve: {str(e)}"
        )


@router.put("/vacuum/vent_valve")
async def set_vent_valve(request: Request, valve: GasValveRequest):
    """Set vent valve state."""
    try:
        await request.app.state.service.equipment.set_vent_valve(valve.open)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set vent valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set vent valve: {str(e)}"
        )


@router.put("/vacuum/mechanical_pump/state")
async def set_mech_pump_state(request: Request, pump: VacuumPumpRequest):
    """Set mechanical pump state."""
    try:
        await request.app.state.service.equipment.set_mechanical_pump_state(pump.start)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set mechanical pump state: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set mechanical pump state: {str(e)}"
        )


@router.put("/vacuum/booster_pump/state")
async def set_booster_pump_state(request: Request, pump: VacuumPumpRequest):
    """Set booster pump state."""
    try:
        await request.app.state.service.equipment.set_booster_pump_state(pump.start)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set booster pump state: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set booster pump state: {str(e)}"
        )


@router.put("/feeder/{feeder_id}/state")
async def set_feeder_state(
    request: Request,
    feeder_id: Literal[1, 2],
    state: FeederStateRequest
):
    """Set feeder running state."""
    try:
        await request.app.state.service.equipment.set_feeder_state(feeder_id, state.running)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder {feeder_id} state: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder {feeder_id} state: {str(e)}"
        )


@router.put("/feeder/{feeder_id}/frequency")
async def set_feeder_frequency(
    request: Request,
    feeder_id: Literal[1, 2],
    feeder: FeederRequest
):
    """Set feeder frequency."""
    try:
        await request.app.state.service.equipment.set_feeder_frequency(feeder_id, feeder.frequency)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder {feeder_id} frequency: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder {feeder_id} frequency: {str(e)}"
        )


@router.put("/deagglomerator/{deagg_id}/duty_cycle")
async def set_deagglomerator_duty_cycle(
    request: Request,
    deagg_id: Literal[1, 2],
    deagg: DeagglomeratorRequest
):
    """Set deagglomerator duty cycle."""
    try:
        await request.app.state.service.equipment.set_deagglomerator_duty_cycle(deagg_id, deagg.duty_cycle)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set deagglomerator {deagg_id} duty cycle: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set deagglomerator {deagg_id} duty cycle: {str(e)}"
        )


@router.put("/nozzle/select")
async def select_nozzle(request: Request, nozzle: NozzleSelectRequest):
    """Select active nozzle."""
    try:
        await request.app.state.service.equipment.select_nozzle(nozzle.nozzle)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to select nozzle: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to select nozzle: {str(e)}"
        )


@router.put("/nozzle/shutter")
async def set_shutter_state(request: Request, shutter: ShutterRequest):
    """Set shutter state."""
    try:
        await request.app.state.service.equipment.set_shutter_state(shutter.open)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set shutter state: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set shutter state: {str(e)}"
        )
