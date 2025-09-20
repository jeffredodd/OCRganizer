"""Setup configuration for OCRganizer."""

from pathlib import Path

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            # Remove version specifiers for setup.py
            req = line.split(">=")[0].split("==")[0].split("<=")[0]
            if req:
                requirements.append(line)

setup(
    name="OCRganizer",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered PDF document organization and categorization system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/OCRganizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Archiving",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.1.1",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.12.0",
            "black>=24.3.0",
            "flake8>=7.0.0",
            "mypy>=1.9.0",
            "isort>=5.13.0",
        ],
        "local-ai": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pdf-categorizer=cli:main",
            "pdf-categorizer-web=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
        "templates": ["*.html"],
        "static": ["*.css", "*.js"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/OCRganizer/issues",
        "Source": "https://github.com/yourusername/OCRganizer",
        "Documentation": "https://github.com/yourusername/OCRganizer/wiki",
    },
)
