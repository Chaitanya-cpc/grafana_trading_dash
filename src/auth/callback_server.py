"""
Local callback server for handling OAuth redirects automatically.
"""

import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Callable
from loguru import logger


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks."""
    
    def do_GET(self):
        """Handle GET requests to capture OAuth callback."""
        try:
            # Parse the URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Check if this is the callback with request_token
            if 'request_token' in query_params:
                request_token = query_params['request_token'][0]
                status = query_params.get('status', [''])[0]
                action = query_params.get('action', [''])[0]
                
                logger.info(f"Callback received: status={status}, action={action}")
                
                # Store the request token in the server instance
                self.server.request_token = request_token
                self.server.callback_received = True
                
                # Send success response to browser
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Zerodha Authentication</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 50px; text-align: center; }
                        .success { color: #28a745; }
                        .container { max-width: 600px; margin: 0 auto; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="success">✅ Authentication Successful!</h1>
                        <p>Your Zerodha account has been successfully connected.</p>
                        <p>You can now close this browser window and return to your application.</p>
                        <hr>
                        <small>Zerodha Dashboard - Authentication Complete</small>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                
            else:
                # Handle error or invalid callback
                error = query_params.get('error', ['Unknown error'])[0]
                logger.error(f"Callback error: {error}")
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authentication Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 50px; text-align: center; }}
                        .error {{ color: #dc3545; }}
                        .container {{ max-width: 600px; margin: 0 auto; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">❌ Authentication Failed</h1>
                        <p>Error: {error}</p>
                        <p>Please try again or check your API credentials.</p>
                        <hr>
                        <small>Zerodha Dashboard - Authentication Error</small>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
                
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override to suppress default HTTP server logs."""
        pass


class CallbackServer:
    """
    Local HTTP server to capture OAuth callbacks automatically.
    """
    
    def __init__(self, host: str = "localhost", port: int = 3000):
        """
        Initialize callback server.
        
        Args:
            host: Server host (default: localhost).
            port: Server port (default: 3000).
        """
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.request_token: Optional[str] = None
        self.callback_received = False
        
        logger.info(f"CallbackServer initialized on {host}:{port}")
    
    def start(self) -> bool:
        """
        Start the callback server in a separate thread.
        
        Returns:
            True if server started successfully.
        """
        try:
            # Create HTTP server
            self.server = HTTPServer((self.host, self.port), CallbackHandler)
            self.server.request_token = None
            self.server.callback_received = False
            
            # Start server in separate thread
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"Callback server started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            return False
    
    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Callback server stopped")
    
    def wait_for_callback(self, timeout: int = 300) -> Optional[str]:
        """
        Wait for OAuth callback and return request token.
        
        Args:
            timeout: Maximum time to wait in seconds (default: 5 minutes).
            
        Returns:
            Request token if received, None if timeout.
        """
        logger.info(f"Waiting for callback (timeout: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.server and self.server.callback_received:
                self.request_token = self.server.request_token
                logger.info("Callback received successfully")
                return self.request_token
            
            time.sleep(0.5)  # Check every 500ms
        
        logger.warning("Callback timeout reached")
        return None
    
    def get_callback_url(self) -> str:
        """
        Get the callback URL for this server.
        
        Returns:
            Full callback URL.
        """
        return f"http://{self.host}:{self.port}/callback"
