#!/usr/bin/env python3.11
"""
SYNAX Live Web Server & Online Playground API
=============================================
Tarayıcıdan gelen .sx niyetlerini gerçek zamanlı olarak Apple M1 / C / NEON / Metal GPU
motorunda derleyip evrim sonuçlarını JSON olarak döndüren web sunucusu.
"""
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from synax_sdk import compile_intent

PORT = 8080
BASE_DIR = "/Users/o.farukaydin/.gemini/antigravity/scratch/synax"

class SynaxWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/evolve":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body) if body else {}
            sx_text = payload.get("sx", "niyet: derin rezonans hesapla")
            is_tiny = payload.get("tiny_mcu", False)

            kernel = compile_intent(sx_text, simulate_tiny_mcu=is_tiny)
            sample_a = [1.25, 2.50, -0.5, 4.0] * 25_000
            sample_b = [0.80, 1.10, 3.0,  0.5] * 25_000
            res = kernel.run(sample_a, sample_b, bias=-0.1)

            response_data = {
                "operation": kernel.intent.operation,
                "formula": kernel.intent.formula_desc,
                "winner_dna": res["secilen_dna"],
                "best_us": res["sure_us"],
                "healed": res["onarilan_bozuk_veri"],
                "preview": res["sonuc_ilk_5"]
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_error(404)

if __name__ == "__main__":
    print(f"🌐 SYNAX Resmi Web Sitesi & Canlı Playground Sunucusu: http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), SynaxWebHandler).serve_forever()

