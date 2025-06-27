#!/bin/bash
# setup_git_hooks.sh

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create a symlink to our pre-tag hook
ln -sf ../../.git-hooks/pre-tag .git/hooks/pre-tag

# Make it executable
chmod +x .git/hooks/pre-tag

# Install pre-commit and pre-push hooks
pre-commit install
pre-commit install --hook-type pre-push

echo "Git hooks have been set up successfully!"
