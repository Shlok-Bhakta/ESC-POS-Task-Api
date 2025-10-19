import requests
import json

# BASE_URL = "http://kiwi:33025"
BASE_URL = "http://127.0.0.1:5000"

def test_health():
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_queue():
    print("Testing /queue endpoint...")
    response = requests.get(f"{BASE_URL}/queue")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_print_task(task_data):
    print(f"Testing /print-task with priority: {task_data.get('priority', 'normal')}")
    response = requests.post(
        f"{BASE_URL}/print-task",
        json=task_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_print_raw(html_content):
    print("Testing /print-raw endpoint...")
    response = requests.post(
        f"{BASE_URL}/print-raw",
        json={"html": html_content},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

if __name__ == "__main__":
    test_health()
    test_queue()
    
    # test_print_task({
    #     "title": "SOCATTTT",
    #     "description": "Over the net baby",
    #     "priority": "high",
    #     "due_date": "May, 23"
    # })
    
    # test_print_raw("""
    # <!DOCTYPE html>
    # <html>
    # <head>
    #     <style>
    #         html, body { margin: 0; padding: 0; background: white; width: 576px; }
    #         .content { padding: 20px; }
    #         h1 { font-size: 48px; text-align: center; margin: 20px 0; }
    #         p { font-size: 24px; text-align: center; margin: 20px 0; }
    #     </style>
    # </head>
    # <body>
    #     <div class="content">
    #         <h1>Raw HTML Test</h1>
    #         <p>This is a test of the raw HTML printing endpoint!</p>
    #     </div>
    # </body>
    # </html>
    # """)
    
    # test_print_task({
    #     "title": "Normal Priority Task",
    #     "description": "This is a normal priority task with a blue border.",
    #     "priority": "normal"
    # })
    
    # test_print_task({
    #     "title": "High Priority Task",
    #     "description": "This is a high priority task with an orange border.",
    #     "priority": "high"
    # })
    
    # test_print_task({
    #     "title": "Urgent Priority Task",
    #     "description": "This is an urgent priority task with a red border. Needs immediate attention!",
    #     "priority": "urgent"
    # })
