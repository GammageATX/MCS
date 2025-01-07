# MCS Services Documentation

## Service Architecture Overview

### UI Service (Port 8000)

Primary interface service for web frontend.

### Configuration Service (Port 8001)

Manages system configuration and schemas.

#### Endpoints

- `GET /config/list` - List available configurations
- `GET /config/{name}` - Get configuration by name
- `PUT /config/{name}` - Update configuration
- `POST /config/validate/{name}` - Validate configuration
- `GET /config/schema/list` - List available schemas
- `GET /config/schema/{name}` - Get schema definition

### State Service (Port 8002)

Manages system state and transitions.

#### Endpoints

- `GET /state` - Get current state
- `GET /transitions` - Get valid state transitions
- `POST /transition/{new_state}` - Transition to new state
- `GET /history` - Get state history

### Communication Service (Port 8003)

Handles real-time communication and hardware control.

**Key Requirements:**

- Support independent operation of PLC and feeder systems
- Hardware control endpoints work with partial system availability
- Graceful handling of disconnected components

#### WebSocket Endpoints

- `WS /ws/state` - Real-time system state updates

#### Hardware Control Endpoints

##### Gas Control

- `POST /gas/main/flow` - Set main gas flow rate
- `POST /gas/feeder/flow` - Set feeder gas flow rate
- `POST /gas/main/valve` - Control main gas valve
- `POST /gas/feeder/valve` - Control feeder gas valve

##### Feeder Control

- `POST /feeder/{feeder_id}/frequency` - Set feeder frequency
- `POST /feeder/{feeder_id}/start` - Start feeder
- `POST /feeder/{feeder_id}/stop` - Stop feeder

##### Deagglomerator Control

- `POST /deagg/{deagg_id}/settings` - Set deagglomerator parameters (speed via duty cycle 20-35%, fixed 500Hz frequency)

##### Nozzle Control

- `POST /nozzle/select` - Select active nozzle
- `POST /nozzle/shutter/open` - Open nozzle shutter
- `POST /nozzle/shutter/close` - Close nozzle shutter

##### Vacuum Control

- `POST /vacuum/gate` - Control gate valve
- `POST /vacuum/vent/open` - Open vent valve
- `POST /vacuum/vent/close` - Close vent valve
- `POST /vacuum/mech/start` - Start mechanical pump
- `POST /vacuum/mech/stop` - Stop mechanical pump
- `POST /vacuum/booster/start` - Start booster pump
- `POST /vacuum/booster/stop` - Stop booster pump

##### Motion Control

- `POST /motion/jog/{axis}` - Jog single axis
- `POST /motion/move` - Execute coordinated move
- `POST /motion/home/set` - Set home position
- `POST /motion/home/move` - Move to home position

### Process Service (Port 8004)

Manages process sequences and patterns.

#### Sequence Endpoints

- `GET /process/sequences` - List sequences
- `GET /process/sequences/{sequence_id}` - Get sequence
- `POST /process/sequences/{sequence_id}/start` - Start sequence
- `POST /process/sequences/{sequence_id}/stop` - Stop sequence
- `GET /process/sequences/{sequence_id}/status` - Get sequence status

#### Pattern Endpoints

- `GET /process/patterns` - List patterns
- `POST /process/patterns/generate` - Generate pattern

#### Parameter Endpoints

- `GET /process/parameters` - List parameter sets

### Data Collection Service (Port 8005)

Handles process data collection and storage.

#### Endpoints

- `POST /data_collection/data/start/{sequence_id}` - Start data collection
- `POST /data_collection/data/stop` - Stop data collection
- `POST /data_collection/data/record` - Record spray event


## Common Features

### Health Check

All services expose a health endpoint:

```json
GET /health
{
  "status": "ok|error|starting|stopped",
  "service": "service_name",
  "version": "1.0.0",
  "is_running": true,
  "uptime": 123.45,
  "error": null,
  "components": {
    "component1": {
      "status": "ok|error",
      "error": null
    }
  }
}
```

For UI and simple services, a basic health check is sufficient. For services with critical components (like Communication Service), component health should be included in the response.
