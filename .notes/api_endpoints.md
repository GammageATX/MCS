# MCS API Endpoints Documentation

## Overview

The MCS system consists of multiple services, each with its own API endpoints. All services follow RESTful principles and return JSON responses.

## Base URLs

- Process Service: `http://localhost:8003`
- Communication Service: `http://localhost:8001`
- Config Service: `http://localhost:8002`
- Data Collection Service: `http://localhost:8004`

## Common Response Formats

All endpoints follow these response patterns:

- Success responses include appropriate HTTP status codes (200, 201, etc.)
- Error responses include:
  - HTTP status code (4xx for client errors, 5xx for server errors)
  - Error message in the response body
  - Additional details when available

## Process Service Endpoints

### Health Check
- `GET /health`
  - Returns service health status
  - Response: `ServiceHealth` object

### Parameters
- `GET /parameters`
  - List all available parameters
  - Response: `ParameterListResponse` containing parameter IDs

- `POST /parameters`
  - Create a new parameter set
  - Body: `Parameter` object
  - Response: Created parameter ID

- `GET /parameters/{id}`
  - Get parameter set by ID
  - Response: `ParameterResponse` containing parameter details

- `PUT /parameters/{id}`
  - Update parameter set
  - Body: `Parameter` object
  - Response: Updated parameter ID

- `DELETE /parameters/{id}`
  - Delete parameter set
  - Response: Success message

### Nozzles
- `GET /parameters/nozzles`
  - List all available nozzles
  - Response: `NozzleListResponse` containing nozzle IDs

- `POST /parameters/nozzles`
  - Create a new nozzle configuration
  - Body: `Nozzle` object
  - Response: Created nozzle ID

- `GET /parameters/nozzles/{id}`
  - Get nozzle configuration by ID
  - Response: `NozzleResponse` containing nozzle details

- `PUT /parameters/nozzles/{id}`
  - Update nozzle configuration
  - Body: `Nozzle` object
  - Response: Updated nozzle ID

- `DELETE /parameters/nozzles/{id}`
  - Delete nozzle configuration
  - Response: Success message

### Powders
- `GET /parameters/powders`
  - List all available powders
  - Response: `PowderListResponse` containing powder IDs

- `POST /parameters/powders`
  - Create a new powder configuration
  - Body: `Powder` object
  - Response: Created powder ID

- `GET /parameters/powders/{id}`
  - Get powder configuration by ID
  - Response: `PowderResponse` containing powder details

- `PUT /parameters/powders/{id}`
  - Update powder configuration
  - Body: `Powder` object
  - Response: Updated powder ID

- `DELETE /parameters/powders/{id}`
  - Delete powder configuration
  - Response: Success message

### Patterns
- `GET /patterns`
  - List all available patterns
  - Response: `PatternListResponse` containing pattern IDs

- `POST /patterns`
  - Create a new pattern
  - Body: `Pattern` object
  - Response: Created pattern ID

- `GET /patterns/{id}`
  - Get pattern by ID
  - Response: `PatternResponse` containing pattern details

- `PUT /patterns/{id}`
  - Update pattern
  - Body: `Pattern` object
  - Response: Updated pattern ID

- `DELETE /patterns/{id}`
  - Delete pattern
  - Response: Success message

### Sequences
- `GET /sequences`
  - List all available sequences
  - Response: `SequenceListResponse` containing sequence IDs

- `POST /sequences`
  - Create a new sequence
  - Body: `Sequence` object
  - Response: Created sequence ID

- `GET /sequences/{id}`
  - Get sequence by ID
  - Response: `SequenceResponse` containing sequence details

- `PUT /sequences/{id}`
  - Update sequence
  - Body: `Sequence` object
  - Response: Updated sequence ID

- `DELETE /sequences/{id}`
  - Delete sequence
  - Response: Success message

- `GET /sequences/{id}/status`
  - Get sequence execution status
  - Response: `SequenceStatusResponse`

- `POST /sequences/{id}/start`
  - Start sequence execution
  - Response: Success message

- `POST /sequences/{id}/stop`
  - Stop sequence execution
  - Response: Success message

## Communication Service Endpoints

### Health Check
- `GET /health`
  - Returns service health status
  - Response: `ServiceHealth` object

### Equipment Status
- `GET /equipment/status`
  - Get current equipment status
  - Response: `EquipmentStatusResponse`

### Motion Control
- `POST /motion/home`
  - Home all axes
  - Response: Success message

- `POST /motion/move`
  - Move to position
  - Body: `MotionRequest`
  - Response: Success message

### System Control
- `POST /system/start`
  - Start system
  - Response: Success message

- `POST /system/stop`
  - Stop system
  - Response: Success message

- `POST /system/reset`
  - Reset system
  - Response: Success message

## Config Service Endpoints

### Health Check
- `GET /health`
  - Returns service health status
  - Response: `ServiceHealth` object

### Configuration
- `GET /config`
  - Get current configuration
  - Response: `ConfigResponse`

- `PUT /config`
  - Update configuration
  - Body: `Config` object
  - Response: Updated configuration

### Schemas
- `GET /schemas`
  - List available schemas
  - Response: `SchemaListResponse`

- `GET /schemas/{name}`
  - Get schema by name
  - Response: JSON Schema

## Data Collection Service Endpoints

### Health Check
- `GET /health`
  - Returns service health status
  - Response: `ServiceHealth` object

### Data Collection
- `GET /data/status`
  - Get data collection status
  - Response: `DataCollectionStatusResponse`

- `POST /data/start`
  - Start data collection
  - Response: Success message

- `POST /data/stop`
  - Stop data collection
  - Response: Success message

## Notes

1. All endpoints require appropriate authentication headers
2. Rate limiting may be applied to certain endpoints
3. Bulk operations are not currently supported
4. All timestamps are in ISO 8601 format
5. All measurements use SI units
6. File operations use JSON format
7. Websocket endpoints are available for real-time updates
8. Health check endpoints are available for all services
