# MCS API Endpoints

This document outlines the standardized API endpoint structure for the MicroColdSpray system.

## Common Service Endpoints

All services implement these base endpoints:

```http
GET  /health      - Get service health status
POST /start       - Start service
POST /stop        - Stop service
```

## Process Service (Port 8003)

```http
# Process Control
GET  /health                     - Get service health status
POST /start                      - Start service
POST /stop                       - Stop service

# Patterns
GET    /patterns/                - List all patterns
POST   /patterns/                - Create new pattern
GET    /patterns/{pattern_id}    - Get pattern details
PUT    /patterns/{pattern_id}    - Update pattern
DELETE /patterns/{pattern_id}    - Delete pattern

# Parameters
GET    /parameters/              - List all parameters
POST   /parameters/              - Create parameter
GET    /parameters/{param_id}    - Get parameter details
PUT    /parameters/{param_id}    - Update parameter
DELETE /parameters/{param_id}    - Delete parameter

# Nozzles
GET    /parameters/nozzles                - List all nozzles
POST   /parameters/nozzles                - Create nozzle
GET    /parameters/nozzles/{nozzle_id}    - Get nozzle details
PUT    /parameters/nozzles/{nozzle_id}    - Update nozzle
DELETE /parameters/nozzles/{nozzle_id}    - Delete nozzle

# Powders
GET    /parameters/powders                - List all powders
POST   /parameters/powders                - Create powder
GET    /parameters/powders/{powder_id}    - Get powder details
PUT    /parameters/powders/{powder_id}    - Update powder
DELETE /parameters/powders/{powder_id}    - Delete powder

# Sequences
GET    /sequences/                        - List all sequences
GET    /sequences/{sequence_id}/status    - Get sequence status
POST   /sequences/{sequence_id}/start     - Start sequence
POST   /sequences/{sequence_id}/stop      - Stop sequence
```

## Config Service (Port 8001)

```http
# Service Control
GET  /health                      - Get service health status
POST /start                       - Start service
POST /stop                        - Stop service

# Configuration Management
GET  /config/list                 - List all configs
GET  /config/{name}               - Get config
PUT  /config/{name}               - Update config
POST /config/validate/{name}      - Validate config

# Schema Management
GET  /config/schema/list          - List all schemas
GET  /config/schema/{name}        - Get schema
PUT  /config/schema/{name}        - Update schema
```

## Communication Service (Port 8002)

```http
# Service Control
GET  /health                                      - Get service health status
POST /start                                       - Start service
POST /stop                                        - Stop service

# Equipment State
GET  /equipment/state                             - Get equipment state
GET  /equipment/internal_states                   - Get all internal states
GET  /equipment/internal_states/{state_name}      - Get specific internal state
GET  /equipment/feeders/{feeder_id}              - Get feeder state
GET  /equipment/deagglomerators/{deagg_id}       - Get deagglomerator state

# Gas Control
POST /equipment/gas/main/flow                     - Set main flow
POST /equipment/gas/feeder/flow                   - Set feeder flow
PUT  /equipment/gas/main/valve                    - Set main gas valve
PUT  /equipment/gas/feeder/valve                  - Set feeder gas valve

# Powder Feeders
POST /equipment/feeder/{feeder_id}/frequency      - Set feeder frequency
PUT  /equipment/feeder/{feeder_id}/state         - Set feeder state

# Deagglomerators
POST /equipment/deagg/{deagg_id}/duty_cycle      - Set deagglomerator duty cycle
POST /equipment/deagg/{deagg_id}/frequency       - Set deagglomerator frequency

# Vacuum System
PUT  /equipment/vacuum/gate                       - Set gate valve
PUT  /equipment/vacuum/mechanical_pump/state      - Set mechanical pump state
PUT  /equipment/vacuum/booster_pump/state        - Set booster pump state
PUT  /equipment/vacuum/vent/open                  - Open vent valve
PUT  /equipment/vacuum/vent/close                 - Close vent valve
PUT  /equipment/vacuum/mech/start                 - Start mechanical pump
PUT  /equipment/vacuum/mech/stop                  - Stop mechanical pump
PUT  /equipment/vacuum/booster/start             - Start booster pump
PUT  /equipment/vacuum/booster/stop              - Stop booster pump

# Nozzle System
PUT  /equipment/nozzle/select                     - Select nozzle
PUT  /equipment/nozzle/shutter                    - Set shutter state
PUT  /equipment/nozzle/shutter/open               - Open shutter
PUT  /equipment/nozzle/shutter/close              - Close shutter

# Motion Control
GET  /motion/position                             - Get position
GET  /motion/status                               - Get status
GET  /motion/internal_states                      - Get motion internal states
GET  /motion/internal_states/{state_name}         - Get motion internal state
GET  /motion/state                                - Get state
POST /motion/jog/{axis}                           - Jog axis
POST /motion/move                                 - Move
POST /motion/home/set                             - Set home
POST /motion/home/move                            - Move to home
```

## Data Collection Service (Port 8004)

```http
# Service Control
GET  /health                                      - Get service health status
POST /start                                       - Start service
POST /stop                                        - Stop service

# Data Collection
POST /data_collection/data/start/{sequence_id}    - Start collection
POST /data_collection/data/stop                   - Stop collection
POST /data_collection/data/record                 - Record event
GET  /data_collection/data/{sequence_id}          - Get sequence events
```

## Design Principles

1. Use nouns for resources, verbs for actions
2. Use plural for collections (`/nozzles` vs `/nozzle`)
3. Hierarchical resources use parent/child pattern (`/parameters/nozzles`)
4. Consistent HTTP methods:
   - GET for reading
   - POST for actions/creating
   - PUT for full updates
   - DELETE for removal
5. Clear separation between services
6. Consistent naming across all endpoints
7. Avoid underscores in URLs
8. Actions are at the end of URLs (`/home/move` not `/move/home`)
