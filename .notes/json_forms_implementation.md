# JSON Forms Implementation Plan

## Overview

Implement JSON Forms library to standardize form handling across the Process API frontend, improving validation, type safety, and user experience.

## Prerequisites

1. Install required dependencies:

   ```bash
   npm install @jsonforms/core @jsonforms/react @jsonforms/material-renderers
   ```

## Implementation Phases

### Phase 1: Schema Definition

1. Create schema directory structure:

   ```dir
   frontend/
   ├── src/
   │   ├── schemas/
   │   │   ├── process/
   │   │   │   ├── pattern.schema.ts
   │   │   │   ├── parameter.schema.ts
   │   │   │   ├── nozzle.schema.ts
   │   │   │   ├── powder.schema.ts
   │   │   │   └── sequence.schema.ts
   │   │   └── index.ts
   ```

2. Define JSON Schemas for each entity type:
   - Pattern Schema
   - Parameter Schema
   - Nozzle Schema
   - Powder Schema
   - Sequence Schema

3. Define UI Schemas for layout control:
   - Form layouts
   - Field grouping
   - Conditional rendering
   - Custom field renderers

### Phase 2: Component Development

1. Create reusable JSON Forms components:

   ```dir
   frontend/
   ├── src/
   │   ├── components/
   │   │   ├── forms/
   │   │   │   ├── JsonFormsDialog.tsx
   │   │   │   ├── JsonFormsWrapper.tsx
   │   │   │   └── custom-renderers/
   ```

2. Implement base components:
   - JsonFormsDialog: Reusable dialog with JSON Forms
   - JsonFormsWrapper: Common wrapper with error handling
   - Custom renderers for specific field types

3. Add form validation:
   - Schema-based validation
   - Custom validation rules
   - Error message handling
   - Form submission control

### Phase 3: FileManagement.tsx Refactoring

1. Update state management:
   - Add form data state
   - Add validation state
   - Add loading states

2. Implement new dialog components:
   - CreateEntityDialog
   - EditEntityDialog
   - PreviewEntityDialog

3. Update CRUD operations:
   - Modify create/update handlers
   - Add form validation
   - Improve error handling
   - Add success notifications

### Phase 4: Testing & Documentation

1. Add unit tests:
   - Schema validation tests
   - Component render tests
   - Form submission tests
   - Error handling tests

2. Add integration tests:
   - End-to-end form submission
   - Data validation
   - API integration

3. Update documentation:
   - Component documentation
   - Schema documentation
   - Usage examples
   - Type definitions

## Detailed Tasks

### 1. Schema Implementation

- [ ] Define base types and interfaces
- [ ] Implement Pattern schema and validation
- [ ] Implement Parameter schema and validation
- [ ] Implement Nozzle schema and validation
- [ ] Implement Powder schema and validation
- [ ] Implement Sequence schema and validation
- [ ] Add schema documentation

### 2. Component Development

- [ ] Create JsonFormsDialog component
- [ ] Create JsonFormsWrapper component
- [ ] Implement custom renderers
- [ ] Add error handling
- [ ] Add loading states
- [ ] Add form validation
- [ ] Add type definitions

### 3. FileManagement.tsx Updates

- [ ] Refactor state management
- [ ] Update create operations
- [ ] Update edit operations
- [ ] Update preview functionality
- [ ] Add form validation
- [ ] Improve error handling
- [ ] Add success notifications

### 4. Testing

- [ ] Add schema validation tests
- [ ] Add component render tests
- [ ] Add form submission tests
- [ ] Add error handling tests
- [ ] Add integration tests
- [ ] Add API integration tests

## Success Criteria

1. All forms use JSON Forms library
2. Improved type safety and validation
3. Better error handling and user feedback
4. Consistent form layouts and styling
5. Comprehensive test coverage
6. Complete documentation

## Timeline

1. Phase 1: 2-3 days
2. Phase 2: 3-4 days
3. Phase 3: 2-3 days
4. Phase 4: 2-3 days

Total estimated time: 9-13 days

## Dependencies

1. @jsonforms/core
2. @jsonforms/react
3. @jsonforms/material-renderers
4. TypeScript 4.x+
5. React 17+
6. Material-UI 5+

## Risks and Mitigations

1. Risk: Schema complexity
   - Mitigation: Start with simple schemas, iterate with complexity

2. Risk: Performance impact
   - Mitigation: Implement lazy loading and code splitting

3. Risk: Learning curve
   - Mitigation: Provide documentation and examples

4. Risk: API compatibility
   - Mitigation: Ensure schemas match API contracts

## Future Enhancements

1. Add form state persistence
2. Implement undo/redo functionality
3. Add form autosave
4. Implement form versioning
5. Add custom form layouts
6. Add form templates

## Code Standards

1. Follow TypeScript best practices
2. Use consistent naming conventions
3. Add comprehensive JSDoc comments
4. Follow React best practices
5. Maintain test coverage
6. Document all changes

## Backend Changes Required

### Schema Endpoint Addition

Add schema endpoints to expose JSON Schema for JSON Forms:

1. Add to `process_endpoints.py`:

```python
@router.get(
    "/schemas/{entity_type}",
    response_model=Dict[str, Any],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Schema not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to get schema"}
    }
)
async def get_schema(
    entity_type: str,
    service: ProcessService = Depends(get_process_service)
) -> Dict[str, Any]:
    """Get JSON Schema for entity type."""
    try:
        schema = await service.schema_service.get_schema(entity_type)
        return schema
    except Exception as e:
        logger.error(f"Failed to get schema for {entity_type}: {e}")
        raise create_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get schema: {str(e)}"
        )
```

2. Update Timeline:
   - Backend changes: 0.5 day
   - Total project timeline: 9.5-13.5 days

No other backend changes required as we already have:

- Full CRUD endpoints for all entities
- Robust validation via Pydantic
- Error handling
- Type safety
- Well-defined data models

### Dependencies Added

- Pydantic JSON Schema generation
- FastAPI validation extensions
