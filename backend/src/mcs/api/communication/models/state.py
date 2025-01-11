from pydantic import BaseModel, Field


class ProcessState(BaseModel):
    """Process status."""
    gas_flow_stable: bool = Field(..., description="Gas flow stability")
    powder_feed_active: bool = Field(..., description="Powder feeding active")
    process_ready: bool = Field(..., description="Process ready to start")


class GasState(BaseModel):
    """Gas system state model."""
    main_flow_setpoint: float = Field(..., description="Main gas flow setpoint in SLPM")
    main_flow_actual: float = Field(..., description="Main gas flow measured value in SLPM")
    feeder_flow_setpoint: float = Field(..., description="Feeder gas flow setpoint in SLPM")
    feeder_flow_actual: float = Field(..., description="Feeder gas flow measured value in SLPM")
    main_valve_state: bool = Field(..., description="True if main gas valve is open")
    feeder_valve_state: bool = Field(..., description="True if feeder gas valve is open")


class VacuumState(BaseModel):
    """Vacuum system state model."""
    chamber_pressure: float = Field(..., description="Chamber pressure in Torr")
    gate_valve_state: bool = Field(..., description="True if gate valve is open")
    mechanical_pump_state: bool = Field(..., description="True if mechanical pump is running")
    booster_pump_state: bool = Field(..., description="True if booster pump is running")
    vent_valve_state: bool = Field(..., description="True if vent valve is open")


class FeederState(BaseModel):
    """Feeder state model."""
    running: bool = Field(..., description="True if feeder is running")
    frequency: float = Field(..., description="Feeder frequency in Hz")


class NozzleState(BaseModel):
    """Nozzle state model."""
    active_nozzle: int = Field(..., description="Currently active nozzle ID (1 or 2)")
    shutter_state: bool = Field(..., description="True if shutter is open")


class DeagglomeratorState(BaseModel):
    """Deagglomerator state model."""
    duty_cycle: float = Field(..., description="Duty cycle percentage")


class PressureState(BaseModel):
    """System pressure state model."""
    chamber: float = Field(..., description="Chamber pressure in Torr")
    feeder: float = Field(..., description="Feeder pressure in PSI")
    main_supply: float = Field(..., description="Main gas supply pressure in PSI")
    nozzle: float = Field(..., description="Nozzle pressure in PSI")
    regulator: float = Field(..., description="Regulator pressure in PSI")


class HardwareState(BaseModel):
    """Hardware status model."""
    motion_enabled: bool = Field(..., description="True if motion system is enabled")
    plc_connected: bool = Field(..., description="True if PLC connection is active")
    position_valid: bool = Field(..., description="True if position tracking is valid")


class Position(BaseModel):
    """Position state model."""
    x: float = Field(..., description="X position in mm")
    y: float = Field(..., description="Y position in mm")
    z: float = Field(..., description="Z position in mm")


class AxisStatus(BaseModel):
    """Axis status model."""
    position: float = Field(..., description="Current position in mm")
    in_position: bool = Field(..., description="True if at target position")
    moving: bool = Field(..., description="True if currently moving")
    error: bool = Field(..., description="True if in error state")
    homed: bool = Field(..., description="True if axis is homed")


class SystemStatus(BaseModel):
    """Motion system status model."""
    x_axis: AxisStatus = Field(..., description="X axis status")
    y_axis: AxisStatus = Field(..., description="Y axis status")
    z_axis: AxisStatus = Field(..., description="Z axis status")
    module_ready: bool = Field(..., description="True if motion controller is ready")


class MotionState(BaseModel):
    """Motion system state model."""
    position: Position = Field(..., description="Current position")
    status: SystemStatus = Field(..., description="Motion system status")


class EquipmentState(BaseModel):
    """Complete equipment state model."""
    gas: GasState = Field(..., description="Gas system state")
    vacuum: VacuumState = Field(..., description="Vacuum system state")
    feeder: FeederState = Field(..., description="Feeder state")
    nozzle: NozzleState = Field(..., description="Nozzle system state")
    deagglomerator: DeagglomeratorState = Field(..., description="Deagglomerator state")
    pressure: PressureState = Field(..., description="System pressure state")
    hardware: HardwareState = Field(..., description="Hardware status")
    process: ProcessState = Field(..., description="Process state")
