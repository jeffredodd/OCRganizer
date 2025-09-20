#!/usr/bin/env python3
"""Version management script for automatic version bumping."""

import re
import sys
from pathlib import Path
from typing import Tuple


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def bump_version(version: str, bump_type: str = "patch") -> str:
    """Bump version number.
    
    Args:
        version: Current version string (e.g., "1.2.3")
        bump_type: Type of bump ("major", "minor", "patch")
    
    Returns:
        New version string
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"


def update_version_files(new_version: str) -> None:
    """Update version in all relevant files."""
    files_to_update = [
        "pyproject.toml",
        "setup.py"
    ]
    
    for file_path in files_to_update:
        path = Path(file_path)
        if not path.exists():
            continue
            
        content = path.read_text()
        
        # Update pyproject.toml
        if file_path == "pyproject.toml":
            content = re.sub(
                r'^version = "[^"]+"',
                f'version = "{new_version}"',
                content,
                flags=re.MULTILINE
            )
        
        # Update setup.py
        elif file_path == "setup.py":
            content = re.sub(
                r'version="[^"]+"',
                f'version="{new_version}"',
                content
            )
        
        path.write_text(content)
        print(f"Updated {file_path} to version {new_version}")


def main():
    """Main version management function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/version.py <bump_type>")
        print("bump_type: major, minor, patch")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ["major", "minor", "patch"]:
        print("Error: bump_type must be 'major', 'minor', or 'patch'")
        sys.exit(1)
    
    try:
        current_version = get_current_version()
        new_version = bump_version(current_version, bump_type)
        
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")
        
        update_version_files(new_version)
        print(f"Version bumped to {new_version}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
