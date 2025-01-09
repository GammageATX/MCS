# HTTP Methods Verification Checklist

This document tracks the verification of HTTP methods against REST conventions.

## REST Conventions

- GET: Retrieve data, no side effects
- POST: Create new resources or trigger actions
- PUT: Update existing resources
- DELETE: Remove resources
- PATCH: Partial updates to resources

## Common Service Endpoints

- [x] Health Check
    - [x] GET /health - Returns service health status
    - [x] Correct use of GET (read-only)

- [x] Service Control  
    - [x] POST /start - Starts service
    - [x] POST /stop - Stops service
    - [x] Correct use of POST (actions)

## Equipment Service

### State Endpoints

- [x] GET /equipment/state - Gets current equipment state
- [x] GET /equipment/internal_states - Gets all internal states
- [x] GET /equipment/internal_states/{state_name} - Gets specific state
- [x] GET /equipment/feeders/{feeder_id} - Gets feeder state
- [x] GET /equipment/deagglomerators/{deagg_id} - Gets deagglomerator state

### Gas Control

- [x] POST /equipment/gas/main/flow - Sets flow setpoint (action)
- [x] POST /equipment/gas/feeder/flow - Sets flow setpoint (action)
- [x] PUT /equipment/gas/main/valve - Sets valve state (state change)
- [x] PUT /equipment/gas/feeder/valve - Sets valve state (state change)

### Powder Feeders

- [x] POST /equipment/feeder/{feeder_id}/frequency - Sets frequency (action)
- [x] PUT /equipment/feeder/{feeder_id}/state - Sets running state (state change)

### Deagglomerators

- [x] POST /equipment/deagg/{deagg_id}/frequency - Sets frequency (action)
- [x] POST /equipment/deagg/{deagg_id}/duty_cycle - Sets duty cycle (action)

### Vacuum System

- [x] PUT /equipment/vacuum/gate - Sets gate valve state
- [x] PUT /equipment/vacuum/mechanical_pump/state - Sets pump state
- [x] PUT /equipment/vacuum/booster_pump/state - Sets pump state
- [x] PUT /equipment/vacuum/vent/open - Opens vent valve
- [x] PUT /equipment/vacuum/vent/close - Closes vent valve

### Nozzle Control

- [x] PUT /equipment/nozzle/select - Sets active nozzle
- [x] PUT /equipment/nozzle/shutter - Sets shutter state
- [x] PUT /equipment/nozzle/shutter/open - Opens shutter
- [x] PUT /equipment/nozzle/shutter/close - Closes shutter

## Motion Service

### State

- [x] GET /motion/position - Gets current position
- [x] GET /motion/internal_states - Gets internal states

### Actions

- [x] POST /motion/jog/{axis} - Performs relative move
- [x] POST /motion/move - Executes coordinated move
- [x] POST /motion/home/set - Sets home position
- [x] POST /motion/home/move - Moves to home

## Process Service

### Patterns

- [x] GET /process/patterns - Lists all patterns
- [x] GET /process/patterns/{id} - Gets specific pattern
- [x] POST /process/patterns - Creates new pattern
- [x] PUT /process/patterns/{id} - Updates existing pattern
- [x] DELETE /process/patterns/{id} - Deletes pattern
- [x] POST /process/patterns/{id}/start - Starts pattern execution

### Parameters

- [x] GET /process/parameters - Lists all parameters
- [x] GET /process/parameters/{id} - Gets specific parameter
- [x] POST /process/parameters - Creates new parameter
- [x] PUT /process/parameters/{id} - Updates existing parameter
- [x] DELETE /process/parameters/{id} - Deletes parameter

### Nozzles

- [x] GET /process/nozzles - Lists all nozzles
- [x] GET /process/nozzles/{id} - Gets specific nozzle
- [x] POST /process/nozzles - Creates new nozzle
- [x] PUT /process/nozzles/{id} - Updates existing nozzle
- [x] DELETE /process/nozzles/{id} - Deletes nozzle

### Powders

- [x] GET /process/powders - Lists all powders
- [x] GET /process/powders/{id} - Gets specific powder
- [x] POST /process/powders - Creates new powder
- [x] PUT /process/powders/{id} - Updates existing powder
- [x] DELETE /process/powders/{id} - Deletes powder

## Data Collection Service

### Sequences

- [x] GET /data/sequences - Lists all sequences
- [x] GET /data/sequences/{id} - Gets specific sequence
- [x] POST /data/sequences/{id}/start - Starts collection
- [x] POST /data/sequences/{id}/stop - Stops collection

### Events

- [x] GET /data/events - Lists all events
- [x] GET /data/events/{id} - Gets specific event
- [x] POST /data/events - Records new event
- [x] PUT /data/events/{id} - Updates event
- [x] DELETE /data/events/{id} - Deletes event
- [x] GET /data/sequences/{id}/events - Gets sequence events

## Config Service

### Configs

- [x] GET /config/configs - Lists available configs
- [x] GET /config/configs/{name} - Gets specific config
- [x] PUT /config/configs/{name} - Updates config
- [x] POST /config/configs/validate - Validates config

### Schemas

- [x] GET /config/schemas - Lists available schemas
- [x] GET /config/schemas/{name} - Gets specific schema

## UI Service

- [x] GET / - Serves index page
- [x] GET /health - Returns service health
- [x] GET /monitoring/services/status - Gets services status

## Progress Tracking

- [x] Common Service Endpoints verified
- [x] Equipment Service Endpoints verified
- [x] Motion Service Endpoints verified
- [x] Process Service Endpoints verified
- [x] Data Collection Service Endpoints verified
- [x] Config Service Endpoints verified
- [x] UI Service Endpoints verified

## Key Findings

1. Consistent use of HTTP methods across services:
   - GET for retrieving data
   - POST for actions and resource creation
   - PUT for state changes and updates
   - DELETE for resource removal

2. Clear distinction between:
   - State queries (GET)
   - Actions (POST)
   - State changes (PUT)
   - Resource management (POST/PUT/DELETE)

3. No PATCH endpoints currently implemented
   - Could be useful for partial updates in future

4. WebSocket endpoints properly implemented for:
   - Equipment state updates
   - Motion state updates
   - Combined system state updates
