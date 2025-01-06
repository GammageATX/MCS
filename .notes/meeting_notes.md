# MCS Project Meeting Notes

## 2024-01-03: Project Structure Setup

### Participants

- Development Team
- AI Assistant (Cursor)

### Decisions

1. Adopted monorepo structure for better code organization
2. Selected key technologies:
   - Frontend: React + TypeScript + shadcn/ui
   - Backend: FastAPI + SQLAlchemy
   - Package Managers: pnpm (frontend) + uv (backend)

### Action Items

- [x] Set up monorepo structure
- [x] Configure shared types
- [x] Create project documentation
- [ ] Set up development environment
- [ ] Configure CI/CD pipeline

### Technical Decisions

1. Type Safety
   - Using shared TypeScript types between frontend and backend
   - Strict type checking enabled
   - Pydantic models in backend to match TypeScript types

2. Development Workflow
   - Feature-based directory structure
   - Comprehensive documentation requirements
   - Test-driven development approach

3. Package Management
   - Using uv for Python dependencies (faster, more reliable)
   - Using pnpm for Node.js dependencies (efficient, deterministic)

### Next Steps

1. Complete development environment setup
2. Begin user authentication system implementation
3. Set up initial database schema

## 2024-01-04: Code Consistency Analysis

### Participants

- Development Team
- AI Assistant (Cursor)

### Existing Standards

1. Health Check System
   - Standardized HealthStatus enum (OK, DEGRADED, ERROR, STARTING, STOPPED)
   - Consistent health models (ComponentHealth, ServiceHealth)
   - Common utility functions for health reporting
   - Uniform uptime tracking

2. Error Handling
   - Standardized create_error utility
   - Consistent error response format
   - Clean FastAPI integration
   - Optional detailed error information

3. Development Mode
   - Standardized __main__.py structure
   - Consistent logging configuration
   - Config loading with defaults
   - Hot reload functionality
   - Environment variable overrides

### Key Findings

1. Method Naming Inconsistencies
   - Mixed patterns in equipment service methods (set_* vs start_*/stop_*)
   - More consistent patterns in motion service
   - Need standardization for binary states, values, and actions

2. Error Handling Variations
   - Inconsistent use of create_error utility
   - Mixed direct error creation and try/except patterns
   - Need standardized error handling approach

3. State Management Differences
   - Multiple patterns for state updates
   - Inconsistent callback notifications
   - Mixed async/sync callback handling

4. Validation Implementation
   - Mixed validation locations (model/service/endpoint)
   - Inconsistent use of Pydantic models
   - Varied validation approaches

5. Logging Inconsistencies
   - Different detail levels in log messages
   - Inconsistent formatting patterns
   - Need standardized logging templates

### Justified Variations

1. Hardware-Specific Logic
   - Different protocols (SSH vs PLC)
   - Hardware-specific communication patterns
   - Specialized error handling

2. State Evaluation Rules
   - Component-specific requirements
   - Hardware-dependent logic
   - Safety-critical variations

3. Update Frequencies
   - Performance-based polling rates
   - Hardware-specific timing requirements
   - Real-time monitoring needs

### Action Items

- [ ] Implement standardized method naming convention
- [ ] Create unified error handling pattern
- [ ] Standardize state management approach
- [ ] Consolidate validation strategy
- [ ] Establish logging standards

### Technical Decisions

1. Method Naming
   - Use set_<component>_state() for binary states
   - Use set_<component>_<parameter>() for values
   - Use perform_<action>() for actions

2. Error Handling
   - Standardize use of create_error utility
   - Implement consistent try/except patterns
   - Define clear error status codes

3. State Management
   - Unified state update mechanism
   - Standardized callback handling
   - Consistent async patterns

### Next Steps

1. Create detailed refactoring plan
2. Prioritize critical inconsistencies
3. Implement changes incrementally
4. Update documentation

## 2024-01-04: Code Standardization Review

### Participants

- Development Team
- AI Assistant (Cursor)

### Key Decisions

1. Method Naming Conventions
   - Standardized state control methods with `set_<component>_state` pattern
   - Unified value control methods with descriptive suffixes (e.g., `_rate`)
   - Removed redundant method pairs (e.g., start/stop) in favor of state setters

2. Model Standardization
   - Request models use `Request` suffix
   - State models use `State` suffix
   - All fields include units in descriptions
   - Boolean state fields use `_state` suffix

3. API Endpoint Patterns
   - GET for state retrieval
   - POST for value updates
   - PUT for state changes
   - WebSocket for real-time updates

### Implementation Status

1. Completed Changes
   - Equipment service method names updated
   - API endpoints standardized
   - Request and state models updated
   - Documentation added to development standards

2. Pending Tasks
   - Apply standards to other services
   - Add usage examples to documentation
   - Update tests for renamed methods

### Next Steps

1. Review other services for similar standardization opportunities
2. Create documentation with examples
3. Update test suite to reflect new naming

## Notes for Future Meetings

- Review CI/CD requirements
- Discuss testing strategy
- Plan first sprint goals
