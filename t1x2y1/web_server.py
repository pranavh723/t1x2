"""
Simple web server to keep the bot alive on Render
This exposes a port that Render can use to check if the service is running
"""
import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests with a simple response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        response = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bingo Bot Status</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #4CAF50;
                }
                .status {
                    padding: 10px;
                    background-color: #e8f5e9;
                    border-left: 5px solid #4CAF50;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Bingo Bot Status</h1>
                <div class="status">
                    <p>✅ Bot is running!</p>
                    <p>The Telegram bot is active and ready to receive commands.</p>
                </div>
                <p>To use the bot, search for it on Telegram and start a conversation.</p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Override to use our logger instead of printing to stderr"""
        logger.info("%s - %s" % (self.address_string(), format % args))

def start_web_server():
    """Start a simple web server on a separate thread"""
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8080))
    server_address = ('', port)
    
    httpd = HTTPServer(server_address, SimpleHandler)
    logger.info(f'Starting web server on port {port}...')
    
    # Run the server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True  # Thread will exit when main thread exits
    server_thread.start()
    logger.info(f'Web server running on port {port}')
    
    return httpd

if __name__ == '__main__':
    # This will only run if this file is executed directly
    httpd = start_web_server()
    try:
        # Keep the main thread alive
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Stopping web server...')
        httpd.shutdown()
