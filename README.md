# Micro Cold Spray (MCS) Project

A monorepo containing the frontend and backend components of the Micro Cold Spray project.

## Project Structure

```text
mcs/
├── frontend/     # React frontend application
├── backend/      # FastAPI backend service
├── shared/       # Shared types and utilities
├── docs/         # Project documentation
├── .notes/       # Project notes
└── scripts/      # Development and deployment scripts
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- pnpm (for frontend package management)
- uv (for Python package management)

### Installation

1. Install uv for Python package management:

    ```bash
    pip install uv
    ```

2. Install pnpm for frontend package management:

    ```bash
    npm install -g pnpm
    ```

3. Install dependencies:

    ```bash
    # Install frontend dependencies
    pnpm install

    # Install backend dependencies
    cd backend
    uv venv
    uv pip install -r requirements.txt
    ```

### Development

1. Start the frontend development server:

    ```bash
    pnpm --filter frontend dev
    ```

2. Start the backend development server:

    ```bash
    cd backend
    uvicorn src.main:app --reload
    ```

## Contributing

Please refer to the contributing guidelines in the `docs` directory.

## License

[Add your license information here]
