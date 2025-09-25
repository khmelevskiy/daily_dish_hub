#!/bin/bash
# Script to update the detect-secrets baseline file.
# Run this script after adding new secrets to the codebase to update the baseline.
set -e

echo "Installing detect-secrets..."
uv pip install detect-secrets

echo "Creating baseline if it doesn't exist..."
if [ ! -f .secrets.baseline ]; then
    echo "Creating new baseline..."
    uv run detect-secrets scan . > .secrets.baseline
else
    echo "Updating existing baseline..."
    uv run detect-secrets scan --baseline .secrets.baseline .
fi

echo "Done!"
