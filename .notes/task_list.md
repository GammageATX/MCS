# MCS Project Task List

## Current Sprint

### High Priority

- [ ] Communication Service Enhancements
    - [ ] Implement missing hardware control endpoints
        - [x] Gas control endpoints
        - [x] Feeder control endpoints
        - [x] Deagglomerator control endpoint (via duty cycle 20-35%, fixed 500Hz frequency)
        - [x] Nozzle control endpoints (shutter open/close)
        - [x] Vacuum control endpoints (vent, mechanical pump, booster pump)
        - [x] Motion control endpoints
    - [ ] Enhanced health check implementation
        - [ ] Component-level status tracking
        - [ ] Graceful component handling
        - [ ] Partial system operation support
    - [ ] Independent operation support
        - [ ] PLC/Feeder separation
        - [ ] Component status tracking
        - [ ] Selective feature disabling

### Medium Priority

- [ ] Service Architecture Improvements
    - [ ] Standardize service patterns
    - [ ] Base service class implementation
    - [ ] Error handling utilities

### Low Priority

- [ ] System Documentation
    - [ ] API Documentation
    - [ ] Operation manual updates
    - [ ] Component interaction documentation

## Notes

- Focus on hardware control functionality
- Maintain independent operation capability
- Keep health reporting simple and useful
