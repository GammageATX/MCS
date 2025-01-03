# MCS Project Directory Structure

## Root Directory

```directory_structure
mcs/
├── .notes/                 # Project documentation and planning
│   ├── project_overview.md # Project goals and architecture
│   ├── task_list.md       # Current tasks and backlog
│   └── directory_structure.md # This file
│
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── features/      # Feature-specific components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utilities and helpers
│   │   ├── pages/         # Page components
│   │   └── styles/        # Global styles
│   └── public/            # Static assets
│
├── backend/              # FastAPI backend service
│   ├── src/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality
│   │   ├── db/           # Database models
│   │   ├── schemas/      # Pydantic models
│   │   └── services/     # Business logic
│   └── tests/            # Backend tests
│
├── shared/              # Shared types and utilities
│   └── src/
│       ├── types/       # TypeScript interfaces
│       └── utils/       # Shared utilities
│
├── scripts/            # Development and deployment scripts
│   ├── setup.ps1       # Setup script
│   └── deploy.ps1      # Deployment script
│
└── docs/              # Additional documentation
    ├── api/           # API documentation
    ├── setup/         # Setup guides
    └── architecture/  # Architecture diagrams
```

## Key Files

- `.cursorrules` - AI assistant configuration
- `.cursorignore` - Files to ignore in AI analysis
- `package.json` - Root package configuration
- `pyproject.toml` - Python project configuration
- `README.md` - Project overview and setup instructions

## Notes

- All feature-specific code should be in appropriate feature directories
- Shared types must be in shared/src/types
- Tests should mirror the structure of the code they test
- Documentation should be kept up to date with code changes
