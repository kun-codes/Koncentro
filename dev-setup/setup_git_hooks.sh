#!/bin/bash
# setup_git_hooks.sh

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install pre-commit hooks
pre-commit install

echo "Git hooks have been set up successfully!"
