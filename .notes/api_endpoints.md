# MCS API Endpoints

This document outlines the standardized API endpoint structure for the MicroColdSpray system.

## Common Service Endpoints

All services implement these base endpoints:

```http
GET  /health      - Get service health status
POST /start       - Start service
POST /stop        - Stop service
```

## Equipment Service (Port 8002)

Hardware control endpoints for managing equipment state.

```http
# State
GET  /equipment/state                          - Get all equipment state

# Gas Control
POST /equipment/gas/main/flow                  - Set main gas flow rate
POST /equipment/gas/main/valve                 - Set main gas valve state
POST /equipment/gas/feeder/flow                - Set feeder gas flow rate
POST /equipment/gas/feeder/valve               - Set feeder gas valve state

# Powder Feeders
GET  /equipment/feeders                        - Get all feeder states
GET  /equipment/feeders/{id}                   - Get feeder state
POST /equipment/feeders/{id}/frequency         - Set feeder frequency

# Deagglomerators
GET  /equipment/deagglomerators                - Get all deagglomerator states
GET  /equipment/deagglomerators/{id}           - Get deagglomerator state
POST /equipment/deagglomerators/{id}/frequency - Set frequency
POST /equipment/deagglomerators/{id}/duty      - Set duty cycle

# Vacuum System
POST /equipment/vacuum/gate                    - Set gate valve state
POST /equipment/vacuum/pump                    - Set vacuum pump state
```

## Motion Service (Port 8002)

Hardware control endpoints for motion system.

```http
GET  /motion/state                - Get all motion state
GET  /motion/position             - Get current position
POST /motion/position             - Move to position
GET  /motion/home                 - Get home position
POST /motion/home                 - Set current as home
POST /motion/home/move            - Move to home
POST /motion/jog                  - Jog motion
```

## Process Service (Port 8003)

Process configuration and execution management.

```http
# Common Service Endpoints
GET    /health                     - Get service health status
POST   /start                      - Start service
POST   /stop                       - Stop service
POST   /initialize                 - Initialize service

# Patterns
GET    /process/patterns           - List all patterns
GET    /process/patterns/{id}      - Get pattern details
POST   /process/patterns           - Create new pattern
PUT    /process/patterns/{id}      - Update pattern
DELETE /process/patterns/{id}      - Delete pattern
POST   /process/patterns/{id}/start - Start pattern execution

# Parameters
GET    /process/parameters         - List all parameters
GET    /process/parameters/{id}    - Get parameter details
POST   /process/parameters         - Create new parameter
PUT    /process/parameters/{id}    - Update parameter
DELETE /process/parameters/{id}    - Delete parameter

# Nozzles
GET    /process/nozzles           - List all nozzles
GET    /process/nozzles/{id}      - Get nozzle details
POST   /process/nozzles           - Create new nozzle configuration
PUT    /process/nozzles/{id}      - Update nozzle configuration
DELETE /process/nozzles/{id}      - Delete nozzle configuration

# Powders
GET    /process/powders           - List all powders
GET    /process/powders/{id}      - Get powder details
POST   /process/powders           - Create new powder configuration
PUT    /process/powders/{id}      - Update powder configuration
DELETE /process/powders/{id}      - Delete powder configuration

# Sequences
GET    /process/sequences         - List all sequences
GET    /process/sequences/{id}    - Get sequence details
POST   /process/sequences         - Create new sequence
PUT    /process/sequences/{id}    - Update sequence
DELETE /process/sequences/{id}    - Delete sequence
POST   /process/sequences/{id}/start - Start sequence
POST   /process/sequences/{id}/stop  - Stop sequence
GET    /process/sequences/{id}/status - Get sequence status

# WebSocket Endpoints
WS     /process/sequences/ws/{sequence_id} - Real-time sequence status updates
```

## Data Collection Service (Port 8004)

Data collection and management.

```http
# Sequences
GET    /data/sequences                    - List all sequences
GET    /data/sequences/{id}               - Get sequence details
POST   /data/sequences/{id}/start         - Start collecting for sequence
POST   /data/sequences/{id}/stop          - Stop collecting for sequence

# Events
GET    /data/events                       - List all events (with filters)
GET    /data/events/{id}                  - Get event details
POST   /data/events                       - Record new event
PUT    /data/events/{id}                  - Update event
DELETE /data/events/{id}                  - Delete event
GET    /data/sequences/{id}/events        - Get events for sequence
```

## UI Service (Port 8000)

Web interface and monitoring.

```http
GET  /                            - Main monitoring page
GET  /health                      - Get UI service health
GET  /monitoring/services/status  - Get status of all services
```

## Design Principles

1. Use nouns for resources, verbs for actions
2. Use plural for collections (`/nozzles` vs `/nozzle`)
3. Hierarchical resources use parent/child pattern (`/sequences/{id}/events`)
4. Consistent HTTP methods:
   - GET for reading
   - POST for actions/creating
   - PUT for full updates
   - PATCH for partial updates (not currently used)
   - DELETE for removal
5. Clear separation between services
6. Consistent naming across all endpoints
7. Avoid underscores, use hyphens if needed
8. Actions are at the end of URLs (`/home/move` not `/move/home`)
