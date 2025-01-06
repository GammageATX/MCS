"""Motion control endpoints."""

from typing import Dict
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, status
from loguru import logger
import asyncio

from mcs.utils.errors import create_error
from mcs.api.communication.models.state import Position, SystemStatus, MotionState
from mcs.api.communication.models.motion import JogRequest, MoveRequest

router = APIRouter(prefix="/motion", tags=["motion"])


@router.get("/position", response_model=Position)
async def get_position(request: Request) -> Position:
    """Get current position.
    
    Returns:
        Current position
    """
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        position = await service.motion.get_position()
        return position

    except Exception as e:
        error_msg = "Failed to get position"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"{error_msg}: {str(e)}"
        )


@router.get("/status", response_model=SystemStatus)
async def get_status(request: Request) -> SystemStatus:
    """Get motion system status.
    
    Returns:
        System status
    """
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        system_status = await service.motion.get_status()
        return system_status

    except Exception as e:
        error_msg = "Failed to get status"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"{error_msg}: {str(e)}"
        )


@router.websocket("/ws/state")
async def websocket_motion_state(websocket: WebSocket):
    """WebSocket endpoint for motion state updates."""
    try:
        service = websocket.app.state.service
        if not service.is_running:
            await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
            return

        await websocket.accept()
        logger.info("Motion WebSocket client connected")

        # Create queues for state updates
        position_queue = asyncio.Queue()
        status_queue = asyncio.Queue()
        internal_queue = asyncio.Queue()
        
        # Subscribe to state updates
        def position_changed(pos: Position):
            asyncio.create_task(position_queue.put(pos))
            
        def status_changed(status: SystemStatus):
            asyncio.create_task(status_queue.put(status))
            
        def internal_state_changed(states: Dict[str, bool]):
            asyncio.create_task(internal_queue.put(states))
        
        # Register callbacks
        service.motion.on_position_changed(position_changed)
        service.motion.on_status_changed(status_changed)
        service.internal_state.on_motion_state_changed(internal_state_changed)

        try:
            # Send initial state
            position = await service.motion.get_position()
            system_status = await service.motion.get_status()
            internal_states = await service.internal_state.get_motion_states()
            
            await websocket.send_json({
                "state": MotionState(position=position, status=system_status).dict(),
                "internal_states": internal_states
            })

            # Wait for state updates
            while True:
                try:
                    # Wait for any state update
                    done, pending = await asyncio.wait(
                        [
                            asyncio.create_task(position_queue.get()),
                            asyncio.create_task(status_queue.get()),
                            asyncio.create_task(internal_queue.get())
                        ],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                    
                    # Get latest states
                    position = await service.motion.get_position()
                    system_status = await service.motion.get_status()
                    internal_states = await service.internal_state.get_motion_states()
                    
                    # Send update
                    await websocket.send_json({
                        "state": MotionState(position=position, status=system_status).dict(),
                        "internal_states": internal_states
                    })

                except WebSocketDisconnect:
                    logger.info("Motion WebSocket client disconnected")
                    break
                except Exception as e:
                    logger.error(f"Motion WebSocket error: {str(e)}")
                    break

        finally:
            # Unregister callbacks when connection closes
            service.motion.remove_position_changed_callback(position_changed)
            service.motion.remove_status_changed_callback(status_changed)
            service.internal_state.remove_motion_state_changed_callback(internal_state_changed)

    except Exception as e:
        logger.error(f"Failed to handle motion WebSocket connection: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.post("/jog/{axis}")
async def jog_axis(request: Request, axis: str, jog: JogRequest):
    """Perform relative move on single axis."""
    try:
        await request.app.state.service.motion.jog_axis(
            axis=axis.lower(),
            distance=jog.distance,
            velocity=jog.velocity
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to jog {axis} axis: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to jog {axis} axis: {str(e)}"
        )


@router.post("/move")
async def move(request: Request, move: MoveRequest):
    """Execute coordinated move."""
    try:
        await request.app.state.service.motion.move(
            x=move.x,
            y=move.y,
            z=move.z,
            velocity=move.velocity,
            wait_complete=move.wait_complete
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to execute move: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to execute move: {str(e)}"
        )


@router.post("/home/set")
async def set_home(request: Request):
    """Set current position as home."""
    try:
        await request.app.state.service.motion.set_home()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set home: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set home: {str(e)}"
        )


@router.post("/home/move")
async def move_to_home(request: Request):
    """Move to home position."""
    try:
        await request.app.state.service.motion.move_to_home()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to move to home: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to move to home: {str(e)}"
        )


@router.get("/internal_states", response_model=Dict[str, bool])
async def get_motion_internal_states(request: Request) -> Dict[str, bool]:
    """Get all motion-related internal states.
    
    Returns:
        Dict mapping state names to current values for states like:
        - position_valid
        - motion_enabled
        etc.
    """
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        states = await service.internal_state.get_motion_states()
        return states

    except Exception as e:
        error_msg = "Failed to get motion internal states"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"{error_msg}: {str(e)}"
        )


@router.get("/internal_states/{state_name}", response_model=bool)
async def get_motion_internal_state(request: Request, state_name: str) -> bool:
    """Get single motion-related internal state.
    
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

        state = await service.internal_state.get_motion_state(state_name)
        if state is None:
            raise create_error(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"State '{state_name}' not found"
            )
            
        return state

    except Exception as e:
        error_msg = f"Failed to get motion internal state {state_name}"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"{error_msg}: {str(e)}"
        )


@router.get("/state", response_model=MotionState)
async def get_state(request: Request) -> MotionState:
    """Get current motion state."""
    try:
        service = request.app.state.service
        if not service.is_running:
            raise create_error(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                message="Service not running"
            )

        state = await service.motion.get_motion_state()
        return state

    except Exception as e:
        error_msg = "Failed to get motion state"
        logger.error(f"{error_msg}: {str(e)}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"{error_msg}: {str(e)}"
        )
