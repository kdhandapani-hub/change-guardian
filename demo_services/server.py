import argparse, json
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parts=self.path.strip("/").split("/")
        valid=len(parts)==2 and parts[0] in ("accounts","payments","positions") and parts[1] in ("health","smoke","regression")
        failing=valid and parts[0]=="payments" and self.server.scenario=="failure" and parts[1]!="health"
        self.send_response(404 if not valid else 500 if failing else 200)
        self.send_header("Content-Type","application/json");self.end_headers()
        self.wfile.write(json.dumps({"synthetic":True,"service":parts[0],"ok":valid and not failing}).encode())

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--port",type=int,default=8092);p.add_argument("--scenario",choices=["healthy","failure"],default="healthy")
    a=p.parse_args();server=HTTPServer(("127.0.0.1",a.port),Handler);server.scenario=a.scenario
    print("Synthetic service on port",a.port,flush=True);server.serve_forever()
