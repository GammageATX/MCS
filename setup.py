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
        # Core Dependencies
        "fastapi>=0.95.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "PyQt6>=6.4.0",
        "pyyaml>=6.0.1",
        "paramiko>=3.4.0",
        "loguru>=0.7.0",
        "productivity>=0.11.1",
        "asyncssh>=2.13.2",
        "websockets>=12.0",
        "httpx>=0.24.0",
        "jinja2>=3.1.2",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
        "typing_extensions>=4.0.0",
        "jsonschema>=4.17.3",
        "psutil>=5.9.0",
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
