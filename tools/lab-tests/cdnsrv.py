import http.server,socketserver,os
os.chdir('/tmp/ortpkg/package/dist')
class H(http.server.SimpleHTTPRequestHandler):
  def end_headers(self):
    self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Range');super().end_headers()
  def guess_type(self,p):
    return 'text/javascript' if p.endswith(('.mjs','.js')) else 'application/wasm' if p.endswith('.wasm') else 'application/octet-stream'
  def log_message(self,*a):pass
socketserver.ThreadingTCPServer.allow_reuse_address=True
socketserver.ThreadingTCPServer(('',8771),H).serve_forever()
