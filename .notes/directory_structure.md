# MCS Project Directory Structure

## Root Directory

```directory_structure
mcs/
├── .notes/                 # Project documentation and planning
│   ├── project_overview.md # Project goals and architecture
│   ├── task_list.md       # Current tasks and backlog
│   ├── api_endpoints.md    # API documentation
│   └── directory_structure.md # This file
│
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── config/       # Configuration files
│   │   ├── schemas/      # JSON schemas for forms
│   │   └── styles/       # Global styles
│   └── public/           # Static assets
│
├── backend/              # FastAPI backend services
│   ├── src/
│   │   └── mcs/
│   │       ├── api/     # API implementations
│   │       │   ├── process/          # Process service
│   │       │   ├── communication/    # Communication service
│   │       │   ├── config/          # Config service
│   │       │   └── data_collection/ # Data collection service
│   │       ├── utils/   # Shared utilities
│   │       └── core/    # Core functionality
│   ├── data/            # Service data files
│   │   ├── parameters/  # Process parameters
│   │   ├── patterns/    # Motion patterns
│   │   ├── sequences/   # Process sequences
│   │   ├── nozzles/     # Nozzle configurations
│   │   └── powders/     # Powder configurations
│   ├── schemas/         # JSON schemas
│   │   ├── config/      # Configuration schemas
│   │   └── process/     # Process schemas
│   ├── config/          # Service configurations
│   └── tests/           # Backend tests
│
├── shared/              # Shared types and utilities
│   └── src/
│       ├── types/       # TypeScript interfaces
│       └── utils/       # Shared utilities
│
├── scripts/            # Development and deployment scripts
│   ├── setup.ps1      # Setup script
│   └── deploy.ps1     # Deployment script
│
├── logs/              # Application logs
│
└── docs/             # Additional documentation
    ├── api/          # API documentation
    ├── setup/        # Setup guides
    └── architecture/ # Architecture diagrams
```

## Key Files

- `docker-compose.yml` - Container orchestration
- `pyproject.toml` - Python project configuration
- `requirements.txt` - Python dependencies
- `package.json` - Node.js project configuration
- `pnpm-workspace.yaml` - PNPM workspace configuration
- `.cursorrules` - AI assistant configuration
- `.cursorignore` - Files to ignore in AI analysis
- `.flake8` - Python linter configuration
- `.dockerignore` - Docker build exclusions
- `README.md` - Project overview and setup instructions

## Notes

1. All feature-specific code should be in appropriate feature directories
2. Shared types must be in shared/src/types
3. Tests should mirror the structure of the code they test
4. Documentation should be kept up to date with code changes
5. Service data and schemas are organized by service type
6. Configuration files follow a consistent JSON format
7. Each service has its own API implementation in backend/src/mcs/api
8. Frontend components are organized by feature and reusability
