# Micro Cold Spray (MCS) Project Overview

## Project Goal

Build a comprehensive control system for a novel micro cold spray coating process that:

- Aerosolizes submicron-sized powders
- Operates in vacuum environment
- Uses converging-diverging nozzle
- Accelerates particles to supersonic speeds
- Uses stationary nozzle with moving substrate stage for pattern rastering

## Architecture

### Hardware Components

1. **Gas Management System**
   - Pneumatic valves
   - Mass flow controllers
   - Controls aerosol gas flow to nozzle

2. **Vacuum System**
   - Vacuum pumps
   - Gate valve
   - Maintains vacuum chamber environment

3. **Spray Control System**
   - Nozzle shutter mechanism
   - Controls spray process

4. **Powder Management System**
   - Deagglomerator motor for breaking up powder clumps
   - 3-way valves for aerosol flow control
   - Dual hardware setup switching (nozzle/feeder/deagglomerator pairs)

5. **External Powder Feeder**
   - PLC-controlled
   - SSH interface connection
   - Manages powder feed rate

### Software Architecture

#### Frontend (React + TypeScript)

- Modern React application with TypeScript
- Component-based architecture with shadcn/ui
- Real-time monitoring and control interface
- WebSocket integration for live updates

#### Backend (FastAPI + Python)

- Multiple microservices architecture:
- UI Service (Port 8000)
- Configuration Service (Port 8001)
- State Service (Port 8002)
- Communication Service (Port 8003)
- Process Service (Port 8004)
- Data Collection Service (Port 8005)

#### Configuration Management

1. **Component Configuration**
   - Nozzle properties
   - Powder properties
   - Hardware characteristics

2. **Process Configuration**
   - Raster pattern definitions
   - Gas parameter settings
   - Sequence orchestration

## Key Features

1. **System Control**
   - Hardware component initialization
   - Real-time process monitoring
   - Safety checks and interlocks
   - Environment preparation and control

2. **Process Management**
   - Dynamic parameter adjustments
   - Hardware switching control
   - Feeder activation management
   - Pattern rastering execution

3. **Configuration Management**
   - Component configuration editing
   - Process parameter management
   - Sequence file creation and editing
   - Pattern definition tools

4. **Monitoring and Data Collection**
   - Real-time status monitoring
   - Process data logging
   - System state tracking
   - Performance metrics collection

## Technical Requirements

- Type-safe communication between frontend and backend
- Real-time data processing and visualization
- Secure hardware control interfaces
- Comprehensive error handling and safety checks
- Extensive system logging and monitoring

## Development Guidelines

1. **Code Requirements**
   - TypeScript types in shared/
   - API documentation with OpenAPI
   - Comprehensive error handling
   - Unit and integration tests
   - Hardware safety checks

2. **Code Style**
   - Follow standardized service patterns
   - Strict type checking
   - Clear documentation
   - Component isolation
   - Error handling best practices
