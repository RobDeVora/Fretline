import http.server,re,socketserver
data=open('/tmp/stemtest/big.bin','rb').read();st={'n':0}
class H(http.server.BaseHTTPRequestHandler):
  def cors(self):
    self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Range')
  def do_OPTIONS(self):
    self.send_response(204);self.cors();self.end_headers()
  def do_GET(self):
    rg=self.headers.get('Range');st['n']+=1
    if not rg:   # first request: send 10 MB of 40 then drop
      self.send_response(200);self.cors();self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data[:10_000_000]);self.wfile.flush();self.connection.shutdown(2);return
    a=int(re.match(r'bytes=(\d+)-',rg).group(1));chunk=data[a:]
    self.send_response(206);self.cors();self.send_header('Content-Length',str(len(chunk)));self.send_header('Content-Range',f'bytes {a}-{len(data)-1}/{len(data)}');self.end_headers();self.wfile.write(chunk)
  def log_message(self,*a):pass
socketserver.ThreadingTCPServer.allow_reuse_address=True
socketserver.ThreadingTCPServer(('',8772),H).serve_forever()
