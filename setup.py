from setuptools import setup, find_packages

setup(
    name="mcs",
    version="1.0.0",
    description="Micro Cold Spray Control System",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages("backend/src"),
    package_dir={"": "backend/src"},
    include_package_data=True,
    package_data={
        "mcs.ui": [
            "static/**/*",
            "templates/**/*",
        ],
    },
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.2",
        "jsonschema>=4.20.0",
        "productivity>=0.12.0",
        "loguru>=0.7.2",
        "aiohttp>=3.9.1",
        "asyncpg>=0.29.0",
        "numpy>=1.26.2",
        "pandas>=2.1.3",
        "scipy>=1.11.4",
        "scikit-learn>=1.3.2",
        "matplotlib>=3.8.2",
        "seaborn>=0.13.0",
        "plotly>=5.18.0",
        "dash>=2.14.1",
        "dash-bootstrap-components>=1.5.0",
        "dash-core-components>=2.0.0",
        "dash-html-components>=2.0.0",
        "dash-table>=5.0.0",
        "paramiko>=3.3.1",
        "scp>=0.14.5",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-dotenv>=1.0.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pytest-timeout>=2.2.0",
        "pytest-xdist>=3.5.0",
        "black>=23.11.0",
        "isort>=5.12.0",
        "flake8>=6.1.0",
        "mypy>=1.7.1",
        "pylint>=3.0.2",
        "bandit>=1.7.5",
        "safety>=2.3.5",
        "pre-commit>=3.5.0",
    ],
    extras_require={
        "dev": [
            # Testing
            "pytest>=7.3.1",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",

            # Development Tools
            "black>=23.3.0",
            "ruff>=0.1.0",
            "mypy>=1.3.0",
            "isort>=5.12.0",

            # Documentation
            "sphinx>=7.0.1",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ]
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "mcs=mcs.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
