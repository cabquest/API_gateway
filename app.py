from flask import Flask, jsonify, request, Response
from flask_cors import CORS
app = Flask(__name__)
import requests

CORS(app, supports_credentials=True)

MICROSERVICES = {
    # 'auth': 'http://host.docker.internal:9639',
    'auth' : 'http://localhost:9639',
    'booking' : 'http://localhost:9638',
    'ride' : 'http://127.0.0.1:9640',
    'communication' : 'http://127.0.0.1:9641',
}

def forward_request(service_url, path, method, headers, data = None, files = None):
    url = f"{service_url}{path}"
    if files:
        response = requests.request(method=method, url=url, headers=headers, data=data, files=files)
    else:
        response = requests.request(method=method, url=url, headers=headers, json=data)
    return response

@app.route('/<service>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def gateway(service, path):
    if request.method == 'POST':
        if service in MICROSERVICES:    
            service_url = MICROSERVICES[service]
            method = request.method
            headers = {key: value for key, value in request.headers.items() if key != 'Host'}

            if request.content_type.startswith('multipart/form-data'):
                print(request.form)
                print(request.files)
                form_data = request.form
                files = request.files
                forward_url = f'{service_url}/{path}'
    
                payload = {key: value for key, value in form_data.items()}
                file_payload = {key: (file.filename, file.stream, file.content_type) for key, file in files.items()}
                response = requests.post(forward_url, data=payload, files=file_payload)

                return response.content, response.status_code
            else:
                data = request.get_json()
                response = forward_request(service_url, f"/{path}", method, headers, data)
            try:
                response_json = response.json()
                if 'message' in response_json:
                    message = response_json['message']
                return jsonify(response_json), response.status_code, response.headers.items()
            except ValueError:
                return response.content, response.status_code, response.headers.items()
        else:
            return jsonify({"error": "Service not found"}), 404
    elif request.method == 'GET':
         if service in MICROSERVICES:    
            service_url = MICROSERVICES[service]
            method = request.method
            headers = {key: value for key, value in request.headers.items() if key != 'Host'}
            response = requests.request(method=method, url=f'{service_url}/{path}', headers=headers)
            if 'application/json' in response.headers.get('Content-Type', ''):
                print('Response status code:', response.status_code)
                print('Response headers:', response.headers)
                print('Response content:', response.text)  
                print('responsedata:',response)
                return jsonify(response.json())
            else:
                return Response(
                    response.iter_content(chunk_size=8192),
                    content_type=response.headers['Content-Type'],
                    headers={
                        'Content-Disposition': response.headers.get('Content-Disposition', ''),
                        'Content-Length': response.headers.get('Content-Length', '')
                    }
                )

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port = 9637)