"""Equipment control endpoints."""

from typing import Dict, Literal
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, status, Path, Depends
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


# State query endpoint
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
            message=f"{error_msg}: {str(e)}"
        )


# Setpoint command endpoints (POST)
@router.post("/gas/main/flow")
async def set_main_flow(request: Request, flow: GasFlowRequest):
    """Set main gas flow setpoint."""
    try:
        await request.app.state.service.equipment.set_main_flow_setpoint(flow.flow_setpoint)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set main flow: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set main flow: {str(e)}"
        )


@router.post("/gas/feeder/flow")
async def set_feeder_flow(request: Request, flow: GasFlowRequest):
    """Set feeder gas flow setpoint."""
    try:
        await request.app.state.service.equipment.set_feeder_flow_setpoint(flow.flow_setpoint)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder flow: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder flow: {str(e)}"
        )


@router.post("/feeder/{feeder_id}/frequency")
async def set_feeder_frequency(
    request: Request,
    feeder_id: int,
    freq: FeederRequest
):
    """Set feeder frequency setpoint."""
    try:
        await request.app.state.service.equipment.set_feeder_frequency(feeder_id, freq.frequency)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder {feeder_id} frequency: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder {feeder_id} frequency: {str(e)}"
        )


@router.post("/deagg/{deagg_id}/duty_cycle")
async def set_deagglomerator_duty_cycle(
    request: Request,
    deagg_id: Literal[1, 2],
    params: DeagglomeratorRequest
):
    """Set deagglomerator duty cycle."""
    try:
        await request.app.state.service.equipment.set_deagglomerator_duty_cycle(
            deagg_id=deagg_id,
            duty_cycle=params.duty_cycle
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set deagglomerator {deagg_id} duty cycle: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set deagglomerator {deagg_id} duty cycle: {str(e)}"
        )


@router.post("/deagg/{deagg_id}/frequency")
async def set_deagglomerator_frequency(
    request: Request,
    deagg_id: Literal[1, 2],
    params: DeagglomeratorRequest
):
    """Set deagglomerator frequency."""
    try:
        await request.app.state.service.equipment.set_deagglomerator_frequency(
            deagg_id=deagg_id,
            frequency=params.frequency
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set deagglomerator {deagg_id} frequency: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set deagglomerator {deagg_id} frequency: {str(e)}"
        )


# State change endpoints (PUT)
@router.put("/gas/main/valve")
async def set_main_gas_valve(request: Request, valve: GasValveRequest):
    """Set main gas valve state."""
    try:
        await request.app.state.service.equipment.set_main_gas_valve_state(valve.open)
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
        await request.app.state.service.equipment.set_feeder_gas_valve_state(valve.open)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set feeder gas valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set feeder gas valve: {str(e)}"
        )


@router.put("/vacuum/gate")
async def set_gate_valve(request: Request, valve: GateValveRequest):
    """Set gate valve state."""
    try:
        await request.app.state.service.equipment.set_gate_valve_state(valve.position == "open")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set gate valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set gate valve: {str(e)}"
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


@router.put("/nozzle/select")
async def select_nozzle(request: Request, nozzle: NozzleSelectRequest):
    """Set active nozzle state."""
    try:
        await request.app.state.service.equipment.set_nozzle_state(nozzle.nozzle_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set nozzle state: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set nozzle state: {str(e)}"
        )


@router.put("/nozzle/shutter")
async def set_shutter_state(request: Request, shutter: ShutterRequest):
    """Set nozzle shutter state."""
    try:
        await request.app.state.service.equipment.set_shutter_state(shutter.open)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set shutter state: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set shutter state: {str(e)}"
        )


@router.websocket("/ws/state")
async def websocket_equipment_state(websocket: WebSocket):
    """WebSocket endpoint for equipment state updates."""
    try:
        service = websocket.app.state.service
        if not service.is_running:
            await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
            return

        # Accept connection
        await websocket.accept()
        logger.info("Equipment WebSocket client connected")

        # Send initial state
        try:
            initial_state = await service.equipment.get_equipment_state()
            await websocket.send_json(initial_state.dict())
        except Exception as e:
            logger.error(f"Failed to send initial equipment state: {e}")
            await websocket.close()
            return

        # Subscribe to state changes
        async def state_changed(state: EquipmentState):
            try:
                if websocket.application_state == WebSocketDisconnect:
                    await websocket.send_json(state.dict())
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"Failed to send equipment state update: {e}")

        # Register callback
        service.equipment.on_state_changed(state_changed)

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                logger.info("Equipment WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"Error in equipment WebSocket connection: {e}")
                break

    finally:
        # Always clean up
        try:
            service.equipment.remove_state_callback(state_changed)
            if websocket.application_state == WebSocketDisconnect:
                await websocket.close()
        except Exception:
            pass


@router.put("/vacuum/vent/open")
async def open_vent_valve(request: Request):
    """Open vent valve."""
    try:
        await request.app.state.service.equipment.set_vent_valve_state(True)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to open vent valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to open vent valve: {str(e)}"
        )


@router.put("/vacuum/vent/close")
async def close_vent_valve(request: Request):
    """Close vent valve."""
    try:
        await request.app.state.service.equipment.set_vent_valve_state(False)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to close vent valve: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to close vent valve: {str(e)}"
        )


@router.put("/vacuum/mech/start")
async def start_mech_pump(request: Request):
    """Start mechanical pump."""
    try:
        await request.app.state.service.equipment.set_mechanical_pump_state(True)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to start mechanical pump: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to start mechanical pump: {str(e)}"
        )


@router.put("/vacuum/mech/stop")
async def stop_mech_pump(request: Request):
    """Stop mechanical pump."""
    try:
        await request.app.state.service.equipment.set_mechanical_pump_state(False)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to stop mechanical pump: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to stop mechanical pump: {str(e)}"
        )


@router.put("/vacuum/booster/start")
async def start_booster_pump(request: Request):
    """Start booster pump."""
    try:
        await request.app.state.service.equipment.set_booster_pump_state(True)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to start booster pump: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to start booster pump: {str(e)}"
        )


@router.put("/vacuum/booster/stop")
async def stop_booster_pump(request: Request):
    """Stop booster pump."""
    try:
        await request.app.state.service.equipment.set_booster_pump_state(False)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to stop booster pump: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to stop booster pump: {str(e)}"
        )


@router.put("/nozzle/shutter/open")
async def open_shutter(request: Request):
    """Open nozzle shutter."""
    try:
        await request.app.state.service.equipment.set_shutter_state(True)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to open shutter: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to open shutter: {str(e)}"
        )


@router.put("/nozzle/shutter/close")
async def close_shutter(request: Request):
    """Close nozzle shutter."""
    try:
        await request.app.state.service.equipment.set_shutter_state(False)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to close shutter: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to close shutter: {str(e)}"
        )


# Equipment internal state endpoints
@router.get("/internal_states", response_model=Dict[str, bool])
async def get_equipment_internal_states(request: Request) -> Dict[str, bool]:
    """Get all equipment-related internal states.
    
    Returns:
        Dict mapping state names to current values for states like:
        - gas_flow_stable
        - powder_feed_active
        - process_ready
        etc.
    """
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        states = await service.internal_state.get_equipment_states()
        return states

    except Exception as e:
        error_msg = "Failed to get equipment internal states"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"{error_msg}: {str(e)}"
        )


@router.get("/internal_states/{state_name}", response_model=bool)
async def get_equipment_internal_state(request: Request, state_name: str) -> bool:
    """Get single equipment-related internal state.
    
    Args:
        state_name: Name of internal state to get
        
    Returns:
        Current state value
    """
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
            message=f"{error_msg}: {str(e)}"
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
