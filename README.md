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
