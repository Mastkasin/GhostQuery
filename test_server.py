import sys
import os
import traceback
from http.server import HTTPServer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.search import handler
except ImportError:
    print("❌ Error: Could not import handler from api/search.py")
    sys.exit(1)

class SafeLocalHandler(handler):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except Exception as e:
            print(f"\n❌ Uncaught Exception Caught in Wrapper: {e}")
            traceback.print_exc()

def run(port=5050):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, SafeLocalHandler)
    print("==================================================")
    print(" 👻 GhostQuery Socket-Level Test Server Running")
    print("==================================================")
    print(f" Target: http://127.0.0.1:{port}/api/search?q=linux+distros")
    print(" Press Ctrl+C to stop.")
    print("--------------------------------------------------")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        httpd.server_close()

if __name__ == '__main__':
    run()