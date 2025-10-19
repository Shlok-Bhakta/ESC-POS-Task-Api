from flask import Flask, request, jsonify
from escpos.printer import File
from html2image import Html2Image
from PIL import Image
import tempfile
import os
import shutil
from queue import Queue
from threading import Thread
from datetime import datetime

app = Flask(__name__)

PRINTER_DEVICE = os.getenv("PRINTER_DEVICE", "/dev/usb/lp0")
CHROME_PATH = os.getenv("CHROME_PATH", shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome"))
WIDTH = 576

print_queue = Queue()

def render_task_html(task_data):
    title = task_data.get("title", "Task")
    description = "<br />".join(task_data.get("description", "").split("\n"))
    priority = task_data.get("priority", "normal")
    due_date = task_data.get("due_date")
    
    priority_styles = {
        "low": {"border": "4px double black", "icon": "◆"},
        "normal": {"border": "3px solid black", "icon": "●"},
        "high": {"border": "4px solid black", "icon": "▲"},
        "urgent": {"border": "6px double black", "icon": "🚨🚨🚨"},
        "message": {"border": "none", "icon": "💬"},
        "info": {"border": "none", "icon": "ℹ"}
    }
    
    style = priority_styles.get(priority, priority_styles["normal"])
    if style["icon"] is None:
        style["icon"] = "⁉️"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        html, body {{
            margin: 0;
            padding: 0px;
            background: white;
            width: {WIDTH}px;
        }}
        .divider {{
            aspect-ratio: auto;
            height: 40px;
            margin: 0px 0;
        }}
        .priority {{
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin: 0px 0;
        }}
        .title {{
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
            line-height: 1.3;
        }}
        .description {{
            font-size: 24px;
            line-height: 1.8;
            text-align: center;
            margin: 0px 0;
            width: 576px;
            overflow-wrap: anywhere;
        }}
        .due-date {{
            font-size: 22px;
            text-align: center;
            margin: 15px 0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <svg class="divider" viewBox="0 0 2654.285 189.531">
        <path d="M684.809,45.133c34.229-7.489,106.37,0.096,158.835-2.184c25.117-1.092,50.189-4.697,75.329-0.704c62.716,9.962,76.678,35.174,99.705,37.477c8.291-42.721,21.754-36.894,37.88-36.553c18.415,0.802,26.35,23.585,22.617,39.124c-18.983,11.997-5.337-7.578-20.654-23.723c-33.763-1.743-23.725,28.405-17.834,34.396c23.365,23.764,86.471,40.525,99.346-4.258c-7.355,0.802-14.793,4.037-22.203,2.378c-52.151-35.806,51.183-86.14,50.018,6.442c-0.142,11.298,84.307-94.179,150.445-44.998c23.977,17.83,25.482-25.406,84.278-8.365c45.567,13.207,66.264,45.508,86.427,50.349c2.238-19.024,0.832-39.235,26.82-48.553c41.669-8.455,59.624,58.376-0.166,40.258c-1.828,30.916,45.73,46.817,82.009,23.253c8.212-5.364,18.691-9.511,22.341-19.438c5.253-10.949,1.576-27.733-10.977-31.604c-9.65-1.051-10.507,11.779-16.424,16.894c-4.507,0.221-10.922,0.636-12.94-4.452c-0.513-20.284,22.726-33.084,40.534-25.615c24.106,10.111,13.593,31.15,20.627,40.103c1.597,2.033,45.918-21.374,50.912-23.341c95.042-37.432,259.042-18.215,355.842,16.65c17.585,8.018,37.023,12.608,56.433,12.028c11.982,0.964,1.955-23.56-18.608-21.622c-7.825,0.636-15.511,2.184-23.281,2.903c0.636-3.373,1.493-6.691,2.544-9.954c11.834-6.995,26.848-4.396,39.511-1.134c12.691,3.622,16.977,16.728,23.309,26.737c33.823,7.087,28.068-29.343,58.914-11.894c33.701,19.063,413.358,6.431,416.124,7.398c8.439,2.95,2.808,13.223,2.443,19.371c0.166-2.795-328.312-3.692-373.353-3.041c-35.114,0.507-35.708,7.006-49.084,15.197c-23.203,14.208-42.216-28.904-60.63-8.809c-32.227,35.167-94.755,24.781-136.942,2.131c-16.733-8.984-34.837-18.681-54.338-19.412c0.951,16.785,8.42,35.522-8.56,47.336c-27.132,18.877-50.946-18.338-28.865-42.053c3.959-4.252,11.435-6.225,11.268-12.997c-35.034-38.529-99.037-11.592-110.074,5.642c54.964-4.548,60.085,61.85,7.503,55.016c-15.423-2.005-13.546-15.589-1.532-14.174c3.668,0.432,7.249,1.926,10.926,1.583c8.475-0.791,13.101-11.919,9.48-19.621c-17.901-38.079-88.205,31.727-217.46,39.911c-47.052,2.979-40.857-1.284-71.255-11.204c-54.106-16.415-121.085-110.669-177.898-78.525c-3.871,2.35-3.899,7.355-5.253,11.198c1.128-3.199,35.137,23.534,37.708,26.698c10.361,12.75,19.79,23.726,38.172,22.567c-12.285-34.566,11.74-37.162,21.155-32.684c30.451,14.483,8.814,87.828-79.837,42.755c-31.997,11.61-19.55,23.71-66.359-0.664c-82.402,48.732-107.611-20.542-81.354-39.249c9.629-6.86,29.092-4.207,28.394,15.308c-0.114,3.182-3.619,9.924-2.837,12.569c1.776,5.979,18.783,9.939,38.069-21.585c8.812-14.404,16.96-21.457,34.013-23.449c-0.604-4.935,1.872-10.318-25.998-16.57c-34.786-7.803-60.6,11.688-83.494,29.814c-88.05,77.738-132.147,75.104-249.351,38.215c-27.898-8.781-54.848-21.556-83.662-27.045c-28.594-4.24-40.137,20.004-35.085,27.438c7.941,11.683,28.846-10.661,32.54,2.706c2.849,10.31-21.554,26.645-41.476,12.121c-14.946-10.897-14.471-32.045,3.48-43.619c15.965-10.293,33.583-6.145,32.275-14.158c-0.377-2.31-2.878-3.53-5.061-4.377c-23.393-9.071-56.678-27.929-95.862,9.245c-1.134,6.138,4.452,10.645,6.581,15.926c15.346,31.766-15.686,49.136-31.023,39.622c-15.816-12.525-15.871-37.576-2.323-51.843c-36.003-8.272-39.607,6.125-95.45,26.278c-96.493,34.823-104.698-8.109-111.121-15.55c-14.35-1.327-29.253,3.512-39.954,13.189c-4.894,3.76-10.286,10.286-17.198,7.217c-5.641-5.751-9.014-14.986-18.111-16.009c-34.547-3.885-401.605,1.454-406.631-3.665c-33.817-34.494,381-8.128,411.58-17.736C471.9,80.621,473.093,54.981,493,74.012c8.655,8.275,19.091,9.631,30.142,13.314c1.184,0.395,14.711-16.97,16.723-19.012c31.804-32.272,46.162-7.309,33.991,1.043c-3.15,2.162-7.062,2.79-10.768,3.722c-8.027,2.018-8.79,4.979-10.417,12.201C594.622,83.699,614.527,59.212,684.809,45.133"/>
    </svg>
    
    <div class="priority">{style['icon']} {priority} {style['icon']}</div>
    
    <div class="title">{title}</div>
    
    <div class="description">
        {description}
    </div>
    {f'<div class="due-date">Due: {due_date} </div>' if due_date else ''}
    
    <svg class="divider" viewBox="0 0 2654.285 189.531">
        <path d="M684.809,45.133c34.229-7.489,106.37,0.096,158.835-2.184c25.117-1.092,50.189-4.697,75.329-0.704c62.716,9.962,76.678,35.174,99.705,37.477c8.291-42.721,21.754-36.894,37.88-36.553c18.415,0.802,26.35,23.585,22.617,39.124c-18.983,11.997-5.337-7.578-20.654-23.723c-33.763-1.743-23.725,28.405-17.834,34.396c23.365,23.764,86.471,40.525,99.346-4.258c-7.355,0.802-14.793,4.037-22.203,2.378c-52.151-35.806,51.183-86.14,50.018,6.442c-0.142,11.298,84.307-94.179,150.445-44.998c23.977,17.83,25.482-25.406,84.278-8.365c45.567,13.207,66.264,45.508,86.427,50.349c2.238-19.024,0.832-39.235,26.82-48.553c41.669-8.455,59.624,58.376-0.166,40.258c-1.828,30.916,45.73,46.817,82.009,23.253c8.212-5.364,18.691-9.511,22.341-19.438c5.253-10.949,1.576-27.733-10.977-31.604c-9.65-1.051-10.507,11.779-16.424,16.894c-4.507,0.221-10.922,0.636-12.94-4.452c-0.513-20.284,22.726-33.084,40.534-25.615c24.106,10.111,13.593,31.15,20.627,40.103c1.597,2.033,45.918-21.374,50.912-23.341c95.042-37.432,259.042-18.215,355.842,16.65c17.585,8.018,37.023,12.608,56.433,12.028c11.982,0.964,1.955-23.56-18.608-21.622c-7.825,0.636-15.511,2.184-23.281,2.903c0.636-3.373,1.493-6.691,2.544-9.954c11.834-6.995,26.848-4.396,39.511-1.134c12.691,3.622,16.977,16.728,23.309,26.737c33.823,7.087,28.068-29.343,58.914-11.894c33.701,19.063,413.358,6.431,416.124,7.398c8.439,2.95,2.808,13.223,2.443,19.371c0.166-2.795-328.312-3.692-373.353-3.041c-35.114,0.507-35.708,7.006-49.084,15.197c-23.203,14.208-42.216-28.904-60.63-8.809c-32.227,35.167-94.755,24.781-136.942,2.131c-16.733-8.984-34.837-18.681-54.338-19.412c0.951,16.785,8.42,35.522-8.56,47.336c-27.132,18.877-50.946-18.338-28.865-42.053c3.959-4.252,11.435-6.225,11.268-12.997c-35.034-38.529-99.037-11.592-110.074,5.642c54.964-4.548,60.085,61.85,7.503,55.016c-15.423-2.005-13.546-15.589-1.532-14.174c3.668,0.432,7.249,1.926,10.926,1.583c8.475-0.791,13.101-11.919,9.48-19.621c-17.901-38.079-88.205,31.727-217.46,39.911c-47.052,2.979-40.857-1.284-71.255-11.204c-54.106-16.415-121.085-110.669-177.898-78.525c-3.871,2.35-3.899,7.355-5.253,11.198c1.128-3.199,35.137,23.534,37.708,26.698c10.361,12.75,19.79,23.726,38.172,22.567c-12.285-34.566,11.74-37.162,21.155-32.684c30.451,14.483,8.814,87.828-79.837,42.755c-31.997,11.61-19.55,23.71-66.359-0.664c-82.402,48.732-107.611-20.542-81.354-39.249c9.629-6.86,29.092-4.207,28.394,15.308c-0.114,3.182-3.619,9.924-2.837,12.569c1.776,5.979,18.783,9.939,38.069-21.585c8.812-14.404,16.96-21.457,34.013-23.449c-0.604-4.935,1.872-10.318-25.998-16.57c-34.786-7.803-60.6,11.688-83.494,29.814c-88.05,77.738-132.147,75.104-249.351,38.215c-27.898-8.781-54.848-21.556-83.662-27.045c-28.594-4.24-40.137,20.004-35.085,27.438c7.941,11.683,28.846-10.661,32.54,2.706c2.849,10.31-21.554,26.645-41.476,12.121c-14.946-10.897-14.471-32.045,3.48-43.619c15.965-10.293,33.583-6.145,32.275-14.158c-0.377-2.31-2.878-3.53-5.061-4.377c-23.393-9.071-56.678-27.929-95.862,9.245c-1.134,6.138,4.452,10.645,6.581,15.926c15.346,31.766-15.686,49.136-31.023,39.622c-15.816-12.525-15.871-37.576-2.323-51.843c-36.003-8.272-39.607,6.125-95.45,26.278c-96.493,34.823-104.698-8.109-111.121-15.55c-14.35-1.327-29.253,3.512-39.954,13.189c-4.894,3.76-10.286,10.286-17.198,7.217c-5.641-5.751-9.014-14.986-18.111-16.009c-34.547-3.885-401.605,1.454-406.631-3.665c-33.817-34.494,381-8.128,411.58-17.736C471.9,80.621,473.093,54.981,493,74.012c8.655,8.275,19.091,9.631,30.142,13.314c1.184,0.395,14.711-16.97,16.723-19.012c31.804-32.272,46.162-7.309,33.991,1.043c-3.15,2.162-7.062,2.79-10.768,3.722c-8.027,2.018-8.79,4.979-10.417,12.201C594.622,83.699,614.527,59.212,684.809,45.133"/>
    </svg>
</body>
</html>
    """
    return html

def process_print_job(task_data, timestamp):
    try:
        html_content = render_task_html(task_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            hti = Html2Image(
                output_path=tmpdir, 
                size=(WIDTH, 2000),
                custom_flags=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--headless'
                ]
            )
            if CHROME_PATH:
                hti.browser.executable = CHROME_PATH
            
            image_path = hti.screenshot(
                html_str=html_content,
                save_as='task.png'
            )[0]
            
            img = Image.open(os.path.join(tmpdir, image_path))
            img = img.convert('L')
            
            width, height = img.size
            
            top = 0
            for y in range(height):
                row_has_content = False
                for x in range(width):
                    pixel = img.getpixel((x, y))
                    if isinstance(pixel, int) and pixel < 255:
                        row_has_content = True
                        break
                if row_has_content:
                    top = y
                    break
            
            bottom = height
            for y in range(height - 1, top - 1, -1):
                row_has_content = False
                for x in range(width):
                    pixel = img.getpixel((x, y))
                    if isinstance(pixel, int) and pixel < 255:
                        row_has_content = True
                        break
                if row_has_content:
                    bottom = y + 1
                    break
            
            img = img.crop((0, top, width, bottom))
            
            target_width = WIDTH
            img = img.resize((target_width, int(img.height * target_width / img.width)), Image.Resampling.LANCZOS)
            
            img = img.convert('1')
            
            try:
                p = File(PRINTER_DEVICE)
                p.image(img)
                p.text("\n")
                p.cut()
                p.close()
            except Exception as printer_error:
                print(f"Printer error: {printer_error}")
                raise
            
        return True, "printed"
        
    except Exception as e:
        print(f"Error processing print job: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def print_worker():
    import time
    while True:
        task_data, timestamp = print_queue.get()
        if task_data is None:
            break
        process_print_job(task_data, timestamp)
        print_queue.task_done()
        time.sleep(5)

@app.route('/print-task', methods=['POST'])
def print_task():
    try:
        task_data = request.get_json()
        
        if not task_data:
            return jsonify({"error": "No task data provided"}), 400
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        print_queue.put((task_data, timestamp))
        
        return jsonify({
            "success": True,
            "message": "Task queued for printing",
            "timestamp": timestamp
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/print-raw', methods=['POST'])
def print_raw():
    try:
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({"error": "No HTML provided"}), 400
        
        html_content = data['html']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            hti = Html2Image(
                output_path=tmpdir, 
                size=(WIDTH, 2000),
                custom_flags=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--headless'
                ]
            )
            if CHROME_PATH:
                hti.browser.executable = CHROME_PATH
            
            image_path = hti.screenshot(
                html_str=html_content,
                save_as='raw.png'
            )[0]
            
            img = Image.open(os.path.join(tmpdir, image_path))
            img = img.convert('L')
            
            width, height = img.size
            
            top = 0
            for y in range(height):
                row_has_content = False
                for x in range(width):
                    pixel = img.getpixel((x, y))
                    if isinstance(pixel, int) and pixel < 255:
                        row_has_content = True
                        break
                if row_has_content:
                    top = y
                    break
            
            bottom = height
            for y in range(height - 1, top - 1, -1):
                row_has_content = False
                for x in range(width):
                    pixel = img.getpixel((x, y))
                    if isinstance(pixel, int) and pixel < 255:
                        row_has_content = True
                        break
                if row_has_content:
                    bottom = y + 1
                    break
            
            img = img.crop((0, top, width, bottom))
            
            target_width = WIDTH
            img = img.resize((target_width, int(img.height * target_width / img.width)), Image.Resampling.LANCZOS)
            
            img = img.convert('1')
            
            p = File(PRINTER_DEVICE)
            p.image(img)
            p.text("\n")
            p.cut()
            p.close()
        
        return jsonify({
            "success": True,
            "message": "Raw HTML printed"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/queue', methods=['GET'])
def queue_status():
    return jsonify({
        "pending_jobs": print_queue.qsize()
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    worker_thread = Thread(target=print_worker, daemon=True)
    worker_thread.start()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    finally:
        print_queue.put((None, None))
