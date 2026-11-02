"""Turn a local image into the JSON body Cog's HTTP API expects (for Postman / curl).

    python make_request.py cat.jpg            -> writes request.json
Then in Postman: POST http://localhost:5002/predictions, Body -> binary -> request.json,
header Content-Type: application/json.
"""
import base64
import json
import mimetypes
import sys
from pathlib import Path

image = Path(sys.argv[1])
mime = mimetypes.guess_type(image.name)[0] or "image/jpeg"
data_url = f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode()
Path("request.json").write_text(json.dumps({"input": {"image": data_url}}))
print(f"request.json written ({image.name}, {len(data_url) // 1024} KB)")
