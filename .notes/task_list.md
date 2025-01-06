# MCS Project Task List

## Current Sprint

### Service Development Mode Implementation

- [ ] Create standardized __main__.py template
- [ ] Implement development mode for each service:
    - [ ] UI Service
    - [ ] Configuration Service
    - [ ] State Service
    - [ ] Communication Service
    - [ ] Process Service
    - [ ] Data Collection Service
    - [ ] Validation Service
- [ ] Add logging configuration to each service
- [ ] Add config loading with defaults
- [ ] Test hot reload functionality
- [ ] Document development mode usage

## Code Consistency Refactoring

### Phase 0: Leverage Existing Standards

- [ ] Document current standards in utils/
    - [ ] Health check system usage guide
    - [ ] Error handling patterns guide
- [ ] Audit services for compliance with existing standards
- [ ] Create examples of correct usage patterns
- [ ] Add validation for proper standard usage

### Phase 1: Method Naming Standardization

- [ ] Audit current method names across all services
- [ ] Create mapping of old to new method names
- [ ] Update equipment service methods
    - [ ] Standardize binary state methods to set_*_state()
    - [ ] Rename start_*/stop_* methods
    - [ ] Update value setting methods
- [ ] Update motion service methods
- [ ] Update documentation
- [ ] Add tests for renamed methods

### Phase 2: Error Handling Unification

- [ ] Implement standardized error handling utility
- [ ] Update direct error creation instances
- [ ] Standardize try/except blocks
- [ ] Create error code mapping
- [ ] Add error handling tests
- [ ] Update error documentation

### Phase 3: State Management Standardization

- [ ] Create unified state update mechanism
- [ ] Implement standard async callback handler
- [ ] Update state change notifications
- [ ] Add state management tests
- [ ] Document state management patterns

### Phase 4: Validation Consolidation

- [ ] Define validation hierarchy (model/service/endpoint)
- [ ] Create standard validation utilities
- [ ] Update Pydantic models
- [ ] Implement validation chain
- [ ] Add validation tests
- [ ] Update validation documentation

### Phase 5: Logging Standardization

- [ ] Create logging templates
- [ ] Define log levels for different operations
- [ ] Update logging calls
- [ ] Add logging configuration
- [ ] Create logging documentation

## Completed Tasks

### Code Standardization (2024-01-04)

1. Equipment Service Method Names
   - [x] Standardized flow control methods with `_rate` suffix
   - [x] Unified valve control methods with `_state` suffix
   - [x] Standardized pump control methods
   - [x] Updated nozzle control method names

2. API Endpoint Updates
   - [x] Updated endpoint handlers to use new method names
   - [x] Standardized error handling in endpoints
   - [x] Improved endpoint documentation

3. Model Standardization
   - [x] Updated request models with clear documentation
   - [x] Standardized state models with proper units
   - [x] Added consistent field descriptions
   - [x] Fixed model imports and spacing

### Next Steps

1. Apply similar standardization to other services:
   - [ ] Motion service
   - [ ] Process service
   - [ ] Data collection service

2. Update documentation:
   - [ ] Add examples of standardized method usage
   - [ ] Document naming conventions
   - [ ] Update API documentation

3. Testing:
   - [ ] Add tests for renamed methods
   - [ ] Verify endpoint behavior
   - [ ] Test state model validation

## Notes

- Focus on essential health reporting
- Keep implementations simple and maintainable
- Only track critical component status
- Document health check standards
