#!/usr/bin/env bash
nix-shell -p chromium --run "export CHROME_PATH=\$(which chromium) && uv run python main.py"
