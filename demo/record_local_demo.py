from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, subprocess, sys, threading, time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'demo-recording'
OUT.mkdir(exist_ok=True)

class Lab(BaseHTTPRequestHandler):
    server_version = 'CrimsonDemo/1.0'
    sys_version = ''
    def log_message(self, *args):
        pass
    def do_GET(self):
        bodies = {'/': b'<html><title>CrimsonWeb local lab</title><h1>Local demo fixture</h1></html>',
                  '/robots.txt': b'User-agent: *\nDisallow: /admin\n',
                  '/api': b'{"service":"local-demo","status":"ok"}',
                  '/health': b'{"status":"ok"}'}
        body = bodies.get(self.path, b'Not found')
        self.send_response(200 if self.path in bodies else 404)
        self.send_header('Content-Type', 'application/json' if self.path in ('/api', '/health') else 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)
    do_HEAD = do_GET

server = ThreadingHTTPServer(('127.0.0.1', 0), Lab)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
port = server.server_port
args = ['core_engine.py', 'scan', '-t', '127.0.0.1', '-p', str(port), '--no-cve', '--no-recon',
        '--timeout', '1', '--banner-timeout', '2', '--retry', '0', '--port-concurrency', '1',
        '--service-concurrency', '1', '--web-request-delay', '0.01', '--web-sensitive-delay', '0.01',
        '--web-max-global-rate', '600', '--web-max-retries', '0', '--decoy-rate', '0',
        '--output-dir', str(OUT / 'reports'), '--state-file', str(OUT / 'state.json'), '--format', 'json']
start = time.monotonic()
try:
    result = subprocess.run([sys.executable, *args], cwd=ROOT / 'crimson-demo', capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=90,
                            env={**os.environ, 'PYTHONIOENCODING':'utf-8', 'NO_COLOR':'1'})
    (OUT / 'stdout.txt').write_text(result.stdout, encoding='utf-8')
    (OUT / 'stderr.txt').write_text(result.stderr, encoding='utf-8')
    (OUT / 'run.json').write_text(json.dumps({'command': ['python', *args], 'port': port,
                'exit_code':result.returncode, 'duration_seconds':round(time.monotonic()-start,2)}, indent=2), encoding='utf-8')
    print(result.stdout)
    print(result.stderr)
    print('EXIT:',result.returncode)
finally:
    server.shutdown()
    server.server_close()
