# Method Name Verification Checklist

This document tracks the verification of method names against documentation to ensure consistency.

## Common Service Methods

- [x] Health Check Methods
    - [x] Method name - All services use `health()` consistently
    - [x] Health response model naming - Consistent use of ServiceHealth/ComponentHealth
    - [x] Component health naming - Consistent descriptive component names

- [x] Lifecycle Methods  
    - [x] `initialize()` vs documentation - Consistent implementation for basic setup
    - [x] `prepare()` vs documentation - Used for operations requiring running dependencies
    - [x] `start()` vs documentation - Consistent start operation across services
    - [x] `stop()` vs documentation - Consistent cleanup and state reset
    - [x] `shutdown()` vs documentation - Special case for Process Service complete shutdown

## Equipment Service Methods

- [x] Gas Control
    - [x] `set_main_gas_flow()` - Implemented correctly
    - [x] `set_feeder_gas_flow()` - Implemented correctly
    - [x] `set_main_gas_valve_state()` - Implemented correctly
    - [x] `set_feeder_gas_valve_state()` - Implemented correctly

- [x] Powder Feeders
    - [x] `get_feeders()` - Collection endpoint implemented
    - [x] `get_feeder()` - Individual getter implemented
    - [x] `set_feeder_frequency()` - Implemented correctly
    - [x] `set_feeder_state()` - Implemented correctly

- [x] Deagglomerators
    - [x] `get_deagglomerators()` - Collection endpoint implemented
    - [x] `get_deagglomerator()` - Individual getter implemented
    - [x] `set_deagglomerator_frequency()` - Implemented correctly
    - [x] `set_deagglomerator_duty_cycle()` - Implemented correctly

- [x] Vacuum System
    - [x] `set_gate_valve_state()` - Implemented correctly
    - [x] `set_vacuum_pump()` - Split into two methods:
        - `set_mechanical_pump_state()`
        - `set_booster_pump_state()`

Key observations:

- Missing getter methods for feeders and deagglomerators
- Vacuum pump control split into separate mechanical/booster methods
- Additional feeder state control method present
- Consistent error handling and logging across all methods
- All methods properly validate service running state

## Motion Service Methods

- [x] Position Control
    - [x] `get_position()` - Returns current position
    - [x] `move()` - Coordinated move with x,y,z,velocity params
    - [x] `jog_axis()` - Single axis move with distance and velocity

- [x] Home Position
    - [x] `set_home()` - Sets current position as home
    - [x] `move_to_home()` - Moves to home position
    - [x] `get_motion_state()` - Returns full motion state including position

- [x] Status Methods
    - [x] `get_status()` - Returns system status
    - [x] `get_axis_status()` - Returns individual axis status

Key observations:

- All methods properly validate service running state
- Consistent error handling with create_error()
- Complete docstrings and type hints
- Additional status methods for granular control

## Process Service Methods

- [x] Pattern Management
    - [x] `list_patterns()` - Returns list of all patterns
    - [x] `get_pattern()` - Returns specific pattern by ID
    - [x] `create_pattern()` - Creates new pattern
    - [x] `update_pattern()` - Updates existing pattern
    - [x] `delete_pattern()` - Deletes pattern by ID
    - [x] `start_pattern()` - Starts pattern execution

- [x] Parameter Management
    - [x] `list_parameters()` - Returns list of all parameters
    - [x] `get_parameter()` - Returns specific parameter by ID
    - [x] `create_parameter()` - Creates new parameter set
    - [x] `update_parameter()` - Updates existing parameter
    - [x] `delete_parameter()` - Deletes parameter by ID

- [x] Nozzle Management
    - [x] `list_nozzles()` - Returns list of all nozzles
    - [x] `get_nozzle()` - Returns specific nozzle by ID
    - [x] `create_nozzle()` - Creates new nozzle configuration
    - [x] `update_nozzle()` - Updates existing nozzle
    - [x] `delete_nozzle()` - Deletes nozzle by ID

- [x] Powder Management
    - [x] `list_powders()` - Returns list of all powders
    - [x] `get_powder()` - Returns specific powder by ID
    - [x] `create_powder()` - Creates new powder configuration
    - [x] `update_powder()` - Updates existing powder
    - [x] `delete_powder()` - Deletes powder by ID

Key observations:

- All CRUD operations implemented consistently
- Methods follow REST naming conventions
- Proper validation and error handling
- Complete docstrings and type hints
- Consistent use of IDs for resource identification

## Data Collection Service Methods

- [x] Collection Control
    - [x] `start_collection()` - Starts data collection for a sequence
    - [x] `stop_collection()` - Stops current data collection
    - [x] `record_event()` - Records a spray event

- [x] Data Retrieval
    - [x] `get_sequence_events()` - Gets events for a sequence
    - [x] `get_event()` - Gets specific event details
    - [x] `list_events()` - Lists all events with optional filters

Key observations:

- Methods properly validate service running state
- Consistent error handling with create_error()
- Complete docstrings and type hints
- Integration with storage service for persistence
- Proper sequence tracking and event management

## Config Service Methods

- [x] Config Management
    - [x] `list_configs()` - Returns list of available configs
    - [x] `get_config()` - Returns specific config by name
    - [x] `update_config()` - Updates existing config
    - [x] `validate_config()` - Validates config against schema

- [x] Schema Management
    - [x] `get_schema_names()` - Lists available schemas
    - [x] `get_schema()` - Returns specific schema by name
    - [x] `validate_schema()` - Validates schema format

Key observations:

- Proper file handling for config and schema storage
- JSON Schema validation integration
- Automatic schema loading from directory
- Recovery mechanism for failed configs/schemas
- Complete error handling and validation

## Progress Tracking

- [x] Common Service Methods verified
- [x] Equipment Service Methods verified
- [x] Motion Service Methods verified
- [x] Process Service Methods verified
- [x] Data Collection Service Methods verified
- [x] Config Service Methods verified

## Common Service Methods Findings

- [x] Lifecycle Methods
    - [x] `initialize()` - Consistent across all services
    - [x] `prepare()` - Used where needed (Communication, Config, Data Collection)
    - [x] `start()` - Consistent across all services
    - [x] `stop()` - Consistent across services
    - [x] `shutdown()` - Used in Process Service

Key observations:

- All methods follow consistent naming conventions
- No parameters required for lifecycle methods
- Consistent return types (None)
- Proper error handling with create_error()
- Complete docstrings and FastAPI route documentation

## Verification Steps

For each method:

1. Check method name in code matches API documentation
2. Check method name follows our naming conventions
3. Check parameter names are consistent
4. Check return type names are consistent
5. Update either code or documentation to resolve any discrepancies

## Next Steps

1. Start with Common Service Methods
2. Work through each service systematically
3. Document any discrepancies found
4. Make necessary updates to maintain consistency
