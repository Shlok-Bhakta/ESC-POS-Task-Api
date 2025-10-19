#!/usr/bin/env bash

# cleanup() {
#     echo ""
#     echo "Cleaning up printer_output file..."
#     rm -f ./printer_output
#     exit 0
# }

# trap cleanup INT TERM

if [ -e "./printer_output" ]; then
    echo "✓ Found printer_output file - using remote printer"
    nix-shell -p chromium --run "export CHROME_PATH=\$(which chromium) && PRINTER_DEVICE=./printer_output uv run python main.py"
else
    echo "⚠ No printer_output file found"
    echo "For remote printer development, start the socat tunnel first:"
    echo "  tail -f ./printer_output | socat STDIN TCP:192.168.1.205:9100"
    echo ""
    echo "Starting server with default printer device..."
    nix-shell -p chromium --run "export CHROME_PATH=\$(which chromium) && uv run python main.py"
fi

# cleanup
