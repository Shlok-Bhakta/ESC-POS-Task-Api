# Printer Service

Flask service that prints tasks to an ESC/POS thermal printer.

## API

### POST /print-task
Prints a formatted task.

**Request body:**
```json
{
  "title": "Task Title",
  "description": "Task description goes here",
  "priority": "normal"
}
```

Priority options: `low`, `normal`, `high`, `urgent`

**Response:**
```json
{
  "success": true,
  "message": "Task printed successfully"
}
```

### GET /health
Health check endpoint.

## Development

Run locally:
```bash
uv run python main.py
```

### Remote Printer Development

If your printer is connected to a remote machine, use socat to forward the printer device over the network.

**On the remote PC (192.168.1.205) with printer connected:**
```bash
socat TCP-LISTEN:9100,reuseaddr,fork SYSTEM:'cat > /dev/usb/lp0'
```

**On your development machine, start the socat tunnel:**
```bash
tail -f ./printer_output | socat STDIN TCP:192.168.1.205:9100
```

Keep this running in a separate terminal. Then start the development server:
```bash
./run_with_chromium.sh
```

The script will detect the `./printer_output` file and use it automatically.

## Docker

Build and run:
```bash
docker-compose up --build
```

Test:
```bash
curl -X POST http://localhost:5000/print-task \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "description": "This is a test", "priority": "high"}'
```
