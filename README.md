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

## Prerequisites

- Python 3.9+ (3.11 recommended)
- Node.js 18+ (18.19.0 LTS recommended)
- pnpm 8+ (for frontend package management)
- uv (for Python package management)
- PostgreSQL 15+
- Redis 7+

### System Requirements

- Windows 10/11 or Linux
- 8GB RAM minimum
- 20GB free disk space

## Installation

1. Clone the repository:

    ```bash
    git clone [repository-url]
    cd mcs
    ```

2. Install uv for Python package management:

    ```bash
    pip install uv
    ```

3. Install pnpm for frontend package management:

    ```bash
    npm install -g pnpm
    ```

4. Set up environment:

    ```bash
    # Copy example environment files
    cp .env.example .env
    cp backend/.env.example backend/.env
    cp frontend/.env.example frontend/.env
    ```

5. Install dependencies:

    ```bash
    # Install frontend dependencies
    pnpm install

    # Install backend dependencies
    cd backend
    uv venv
    uv pip install -r requirements.txt
    ```

6. Set up databases:

    ```bash
    # Start PostgreSQL and Redis
    # Update connection strings in .env files
    ```

## Development

1. Start the backend services:

    ```bash
    cd backend
    # Activate virtual environment
    .\.venv\Scripts\activate  # Windows
    source .venv/bin/activate # Linux

    # Start the backend
    uvicorn src.main:app --reload --port 8000
    ```

2. Start the frontend development server:

    ```bash
    cd frontend
    pnpm dev
    ```

3. Access the application:
   - Frontend: <http://localhost:5173>
   - Backend API: <http://localhost:8000>
   - API Documentation: <http://localhost:8000/docs>

## Testing

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd frontend
pnpm test
```

## Troubleshooting

1. If you encounter dependency issues:

    ```bash
    cd backend
    rm -rf .venv
    uv venv
    uv pip install -r requirements.txt
    ```

2. For database connection issues:
   - Verify PostgreSQL and Redis are running
   - Check connection strings in .env files
   - Ensure correct permissions are set

## Contributing

Please refer to the contributing guidelines in the `docs` directory.

## License

[Add your license information here]
