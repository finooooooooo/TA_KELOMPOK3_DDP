import webview
from app import create_app
import threading
import sys

# Create the Flask app
app = create_app()

def start_server():
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    # Start Flask in a separate thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    # Create the desktop window
    webview.create_window('CoffeePOS', 'http://127.0.0.1:5000')
    webview.start()
