# Response Models Verification Checklist

This document tracks the verification of response models across all endpoints.

## Common Response Models

- [x] ServiceHealth
    - [x] Consistent use across all /health endpoints
        - Base fields: status, service, version, is_running, uptime, mode, error, components
        - All services properly implement health() method
        - Consistent error handling using create_error_health()
    - [x] Fields match documentation
        - status: HealthStatus enum (OK, ERROR, DEGRADED, STARTING, STOPPED)
        - service: string identifier
        - version: string version number
        - is_running: boolean state
        - uptime: float seconds
        - mode: string (normal, mock, simulation)
        - error: optional string
        - components: Dict[str, ComponentHealth]
    - [x] Error responses consistent
        - All services use create_error_health() helper
        - Consistent error message formatting
        - Proper error status propagation from components

- [x] ErrorResponse
    - [x] Consistent error model across all endpoints
        - All endpoints use create_error() helper
        - Standard error structure: {status: "error", message: str, details?: Dict}
        - Proper exception handling and logging
    - [x] Status codes follow conventions
        - 404: Resource not found
        - 409: Conflict (e.g. already running)
        - 422: Validation failed
        - 500: Internal server error
        - 503: Service unavailable
    - [x] Error messages follow format
        - Clear operation context ("Failed to...")
        - Includes error details when available
        - Consistent logging before raising

## Equipment Service

### State Models

- [x] EquipmentState
    - [x] GET /equipment/state response
        - Comprehensive state model including all subsystems
        - Proper field types and validation
        - Clear field descriptions
    - [x] WebSocket state updates
        - Real-time updates via /ws/state
        - Consistent state format
        - Proper error handling
    - [x] All required fields present
        - gas: GasState
        - vacuum: VacuumState
        - feeder: FeederState
        - nozzle: NozzleState
        - deagglomerator: DeagglomeratorState
        - pressure: PressureState
        - hardware: HardwareState
        - process: ProcessState

- [x] FeederState
    - [x] GET /equipment/feeders/{id} response
        - running: boolean state
        - frequency: float in Hz
    - [x] State update consistency
        - Used in EquipmentState
        - WebSocket updates
        - Individual endpoint

- [x] DeagglomeratorState
    - [x] GET /equipment/deagglomerators/{id} response
        - duty_cycle: float percentage
    - [x] State update consistency
        - Used in EquipmentState
        - WebSocket updates
        - Individual endpoint

### Request Models

- [x] GasFlowRequest
    - flow_rate: float (SLPM)
- [x] GasValveRequest
    - open: boolean
- [x] VacuumPumpRequest
    - start: boolean
- [x] GateValveRequest
    - position: "open" | "closed"
- [x] FeederRequest
    - frequency: float (Hz)
- [x] DeagglomeratorRequest
    - duty_cycle: float (20-35%)

## Motion Service

### State Models

- [x] Position
    - [x] GET /motion/position response
        - x: float (mm)
        - y: float (mm)
        - z: float (mm)
    - [x] Used in MotionState
    - [x] WebSocket updates

- [x] AxisStatus
    - [x] Used in SystemStatus
        - position: float (mm)
        - in_position: boolean
        - moving: boolean
        - error: boolean
        - homed: boolean
    - [x] Consistent field types
    - [x] Clear descriptions

- [x] SystemStatus
    - [x] GET /motion/status response
        - x_axis: AxisStatus
        - y_axis: AxisStatus
        - z_axis: AxisStatus
        - module_ready: boolean
    - [x] Used in MotionState
    - [x] WebSocket updates

- [x] MotionState
    - [x] GET /motion/state response
        - position: Position
        - status: SystemStatus
    - [x] WebSocket updates
        - Real-time updates via /ws/state
        - Consistent state format
        - Proper error handling

### Request Models

- [x] JogRequest
    - axis: str (x, y, z)
    - direction: int (-1, 0, 1)
    - velocity: float (mm/s)

- [x] MoveRequest
    - x: Optional[float] (mm)
    - y: Optional[float] (mm)
    - z: Optional[float] (mm)
    - velocity: float (mm/s)
    - wait_complete: bool

## Process Service

### Base Models

- [x] Nozzle
    - [x] Fields complete
        - name: str
        - manufacturer: str
        - type: NozzleType enum
        - description: str
    - [x] Used in Parameter model
    - [x] Proper validation

- [x] Powder
    - [x] Fields complete
        - name: str
        - type: str
        - size: str
        - manufacturer: str
        - lot: str
    - [x] Used in Parameter model
    - [x] Proper validation

- [x] Pattern
    - [x] Fields complete
        - id: str
        - name: str
        - description: str
        - type: PatternType enum
        - params: Dict[str, Any]
    - [x] Used in Sequence model
    - [x] Proper validation

- [x] Parameter
    - [x] Fields complete
        - name: str
        - created: str
        - author: str
        - description: str
        - nozzle: str
        - main_gas: float
        - feeder_gas: float
        - frequency: int
        - deagglomerator_speed: int
    - [x] Used in Sequence model
    - [x] Proper validation

- [x] Sequence
    - [x] Fields complete
        - metadata: SequenceMetadata
        - steps: List[SequenceStep]
    - [x] Proper validation
    - [x] Step types complete
        - INITIALIZE
        - TROUGH
        - PATTERN
        - PARAMETERS
        - SPRAY
        - SHUTDOWN

### Response Models

- [x] BaseResponse
    - [x] message: str
    - [x] Used consistently for success responses

- [x] NozzleResponse/ListResponse
    - [x] Single/list wrapper models
    - [x] Used in all nozzle endpoints

- [x] PowderResponse/ListResponse
    - [x] Single/list wrapper models
    - [x] Used in all powder endpoints

- [x] PatternResponse/ListResponse
    - [x] Single/list wrapper models
    - [x] Used in all pattern endpoints

- [x] ParameterResponse/ListResponse
    - [x] Single/list wrapper models
    - [x] Used in all parameter endpoints

- [x] SequenceResponse/ListResponse
    - [x] Single/list wrapper models
    - [x] Used in all sequence endpoints

- [x] StatusResponse
    - [x] Fields complete
        - status: ProcessStatus enum
        - details: Optional[Dict[str, Any]]
    - [x] Used in sequence status endpoints
    - [x] WebSocket updates
        - Real-time updates via /ws/{sequence_id}
        - Consistent status format
        - Proper error handling

### Enums

- [x] NozzleType
    - [x] All types defined
        - CONVERGENT_DIVERGENT
        - CONVERGENT
        - VENTED
        - FLAT_PLATE
        - DE_LAVAL
    - [x] Used consistently

- [x] PatternType
    - [x] All types defined
        - LINEAR
        - SERPENTINE
        - SPIRAL
    - [x] Used consistently

- [x] ProcessStatus
    - [x] All states defined
        - IDLE
        - INITIALIZING
        - RUNNING
        - PAUSED
        - COMPLETED
        - ABORTED
        - ERROR
    - [x] Maps to HealthStatus
    - [x] Used consistently

## Data Collection Service

### Base Models

- [x] CollectionSession
    - [x] Fields complete
        - sequence_id: str
        - start_time: datetime
        - collection_params: Dict[str, Any]
    - [x] Proper validation
    - [x] String representation

- [x] SprayEvent
    - [x] Fields complete
        - spray_index: int
        - sequence_id: str (validated)
        - material_type: str
        - pattern_name: str
        - operator: str
        - start_time: datetime
        - end_time: Optional[datetime]
        - powder_size: str
        - powder_lot: str
        - manufacturer: str
        - nozzle_type: str
        - chamber_pressure_start: float (ge=0)
        - chamber_pressure_end: float (ge=0)
        - nozzle_pressure_start: float (ge=0)
        - nozzle_pressure_end: float (ge=0)
        - main_flow: float (ge=0)
        - feeder_flow: float (ge=0)
        - feeder_frequency: float (ge=0)
        - pattern_type: str
        - completed: bool
        - error: Optional[str]
    - [x] Field validation
        - sequence_id format validation
        - numeric field constraints
    - [x] String representation

### Response Models

- [x] BaseResponse
    - [x] message: str
    - [x] Used consistently for success responses
    - [x] Strict validation enabled

- [x] CollectionResponse
    - [x] Extends BaseResponse
    - [x] Used for collection operations

- [x] SprayEventResponse
    - [x] Extends BaseResponse
    - [x] Optional event field
    - [x] Used for single event operations

- [x] SprayEventListResponse
    - [x] Extends BaseResponse
    - [x] events: List[SprayEvent]
    - [x] Used for event listing operations

## Config Service

### Base Models

- [x] BaseResponse
    - [x] timestamp: datetime
    - [x] Used as base for all responses
    - [x] Proper validation

### Request Models

- [x] ConfigRequest
    - [x] Fields complete
        - data: Dict[str, Any]
        - format: str (yaml/json)
        - preserve_format: bool
    - [x] Used in update/validate endpoints
    - [x] Proper validation

- [x] SchemaRequest
    - [x] Fields complete
        - schema_definition: Dict[str, Any]
    - [x] Used in schema update endpoint
    - [x] Proper validation

### Response Models

- [x] MessageResponse
    - [x] Extends BaseResponse
    - [x] message: str
    - [x] Used for success responses

- [x] ConfigResponse
    - [x] Extends BaseResponse
    - [x] Fields complete
        - name: str
        - format: str
        - schema_name: Optional[str]
        - data: Dict[str, Any]
    - [x] Used in get config endpoint

- [x] ConfigListResponse
    - [x] Extends BaseResponse
    - [x] configs: List[str]
    - [x] Used in list configs endpoint

- [x] SchemaResponse
    - [x] Extends BaseResponse
    - [x] Fields complete
        - name: str
        - schema_definition: Dict[str, Any]
    - [x] Used in get schema endpoint

- [x] SchemaListResponse
    - [x] Extends BaseResponse
    - [x] schemas: List[str]
    - [x] Used in list schemas endpoint

### Error Handling

- [x] Consistent error responses
    - [x] 404: Resource not found
    - [x] 422: Validation failed
    - [x] 500: Internal server error
    - [x] 503: Service unavailable

- [x] Error message format
    - [x] Clear operation context
    - [x] Includes error details
    - [x] Proper logging

## Verification Steps

For each response model:

1. Check model definition matches documentation
2. Verify all required fields are present
3. Confirm consistent usage across endpoints
4. Validate error responses
5. Check WebSocket message formats
6. Verify request/response pairs match

## Next Steps

1. Start with common models (ServiceHealth, ErrorResponse)
2. Work through each service systematically
3. Document any inconsistencies found
4. Create list of missing endpoints/methods
5. Update API documentation with findings
