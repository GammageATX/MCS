# MCS Endpoint Implementation Checklist

This document tracks the implementation status of all API endpoints across services.

## Common Service Endpoints

- [x] GET /health
        - [x] Communication Service: `health()`
        - [x] Process Service: `health()`
        - [x] Data Collection Service: `health()`
        - [x] Config Service: `health()`
        - [x] UI Service: `health()`

- [x] POST /start
        - [x] Communication Service: `start_service()`
        - [x] Process Service: `start_service()`
        - [x] Data Collection Service: `start_service()`
        - [x] Config Service: `start_service()`

- [x] POST /stop
        - [x] Communication Service: `stop_service()`
        - [x] Process Service: `stop_service()`
        - [x] Data Collection Service: `stop_service()`
        - [x] Config Service: `stop_service()`

## Equipment Service (Port 8002)

### State

- [x] GET /equipment/state
        - [x] Method: `get_equipment_state()`

### Gas Control

- [x] POST /equipment/gas/main/flow
        - [x] Method: `set_main_gas_flow()`
- [x] POST /equipment/gas/main/valve
        - [x] Method: `set_main_gas_valve()`
- [x] POST /equipment/gas/feeder/flow
        - [x] Method: `set_feeder_gas_flow()`
- [x] POST /equipment/gas/feeder/valve
        - [x] Method: `set_feeder_gas_valve()`

### Powder Feeders

- [x] GET /equipment/feeders
        - [x] Method: `get_feeders()`
- [x] GET /equipment/feeders/{id}
        - [x] Method: `get_feeder()`
- [x] POST /equipment/feeders/{id}/frequency
        - [x] Method: `set_feeder_frequency()`

### Deagglomerators

- [x] GET /equipment/deagglomerators
        - [x] Method: `get_deagglomerators()`
- [x] GET /equipment/deagglomerators/{id}
        - [x] Method: `get_deagglomerator()`
- [x] POST /equipment/deagglomerators/{id}/frequency
        - [x] Method: `set_deagglomerator_frequency()`
- [x] POST /equipment/deagglomerators/{id}/duty
        - [x] Method: `set_deagglomerator_duty()`

### Vacuum System

- [x] POST /equipment/vacuum/gate
        - [x] Method: `set_gate_valve()`
- [x] POST /equipment/vacuum/pump
        - [x] Method: `set_vacuum_pump()`

## Motion Service (Port 8002)

- [x] GET /motion/state
        - [x] Method: `get_motion_state()`
- [x] GET /motion/position
        - [x] Method: `get_position()`
- [x] POST /motion/position
        - [x] Method: `move_to_position()`
- [x] GET /motion/home
        - [x] Method: `get_home_position()`
- [x] POST /motion/home
        - [x] Method: `set_home_position()`
- [x] POST /motion/home/move
        - [x] Method: `move_to_home()`
- [x] POST /motion/jog
        - [x] Method: `jog_motion()`

## Process Service (Port 8003)

### Patterns

- [x] GET /process/patterns
        - [x] Method: `list_patterns()`
- [x] GET /process/patterns/{id}
        - [x] Method: `get_pattern()`
- [x] POST /process/patterns
        - [x] Method: `create_pattern()`
- [x] PUT /process/patterns/{id}
        - [x] Method: `update_pattern()`
- [x] DELETE /process/patterns/{id}
        - [x] Method: `delete_pattern()`
- [x] POST /process/patterns/{id}/start
        - [x] Method: `start_pattern()`

### Parameters

- [x] GET /process/parameters
        - [x] Method: `list_parameters()`
- [x] GET /process/parameters/{id}
        - [x] Method: `get_parameter()`
- [x] POST /process/parameters
        - [x] Method: `create_parameter()`
- [x] PUT /process/parameters/{id}
        - [x] Method: `update_parameter()`
- [x] DELETE /process/parameters/{id}
        - [x] Method: `delete_parameter()`

### Nozzles

- [x] GET /process/nozzles
        - [x] Method: `list_nozzles()`
- [x] GET /process/nozzles/{id}
        - [x] Method: `get_nozzle()`
- [x] POST /process/nozzles
        - [x] Method: `create_nozzle()`
- [x] PUT /process/nozzles/{id}
        - [x] Method: `update_nozzle()`
- [x] DELETE /process/nozzles/{id}
        - [x] Method: `delete_nozzle()`

### Powders

- [x] GET /process/powders
        - [x] Method: `list_powders()`
- [x] GET /process/powders/{id}
        - [x] Method: `get_powder()`
- [x] POST /process/powders
        - [x] Method: `create_powder()`
- [x] PUT /process/powders/{id}
        - [x] Method: `update_powder()`
- [x] DELETE /process/powders/{id}
        - [x] Method: `delete_powder()`

### Sequences

- [x] GET /process/sequences
        - [x] Method: `list_sequences()`
- [x] GET /process/sequences/{id}
        - [x] Method: `get_sequence()`
- [x] POST /process/sequences
        - [x] Method: `create_sequence()`
- [x] PUT /process/sequences/{id}
        - [x] Method: `update_sequence()`
- [x] DELETE /process/sequences/{id}
        - [x] Method: `delete_sequence()`
- [x] POST /process/sequences/{id}/start
        - [x] Method: `start_sequence()`
- [x] POST /process/sequences/{id}/stop
        - [x] Method: `stop_sequence()`

## Data Collection Service (Port 8004)

### Sequences

- [x] GET /data/sequences
        - [x] Method: `list_sequences()`
- [x] GET /data/sequences/{id}
        - [x] Method: `get_sequence()`
- [x] POST /data/sequences/{id}/start
        - [x] Method: `start_sequence_collection()`
- [x] POST /data/sequences/{id}/stop
        - [x] Method: `stop_sequence_collection()`

### Events

- [x] GET /data/events
        - [x] Method: `list_events()`
- [x] GET /data/events/{id}
        - [x] Method: `get_event()`
- [x] POST /data/events
        - [x] Method: `record_event()`
- [x] PUT /data/events/{id}
        - [x] Method: `update_event()`
- [x] DELETE /data/events/{id}
        - [x] Method: `delete_event()`
- [x] GET /data/sequences/{id}/events
        - [x] Method: `get_sequence_events()`

## UI Service (Port 8000)

- [x] GET /
        - [x] Method: `serve_index()`
- [x] GET /health
        - [x] Method: `get_health()`
- [x] GET /monitoring/services/status
        - [x] Method: `get_services_status()`

## Next Steps

1. Search through codebase to verify each endpoint's implementation
2. Check method names match our documentation
3. Verify HTTP methods are correct
4. Ensure response models are consistent
5. Add missing endpoints and methods
6. Update documentation for any discrepancies found
