#!/usr/bin/env bash
set -euxo pipefail

# 1) Check environment
if [ -z "${ELIZA_PATH:-}" ]; then
  echo "ERROR: ELIZA_PATH environment variable is not set."
  echo "Please set ELIZA_PATH to the path containing the ElizaOS code."
  exit 1
fi

# 2) Go to the Eliza path
cd "$ELIZA_PATH"

# 3) Install and build
echo "Installing Node dependencies using pnpm..."
pnpm install

echo "Building ElizaOS..."
pnpm build

echo "======================================================================"
echo "ElizaOS Setup complete."
echo "Next steps:"
echo "  - To start the server: pnpm start --characters=\"characters/johncarter.character.json\""
echo "  - To start the client: pnpm start:client"
echo "======================================================================"
