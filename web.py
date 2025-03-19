import time
import ure
import ujson
import socket
import ntptime
import machine
import network

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
wlan = network.WLAN(network.STA_IF)

def sync_time():
    return
    try:
        ntptime.settime()
        print("Time synced")
    except OSError:
        print("Failed to sync time")

def start_access_point(pwd=""):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    essid = 'MyESP_Hotspot'
    
    if pwd:
        # Protected access point with WPA/WPA2
        ap.config(essid=essid, password=pwd, authmode=network.AUTH_WPA_WPA2_PSK)
    else:
        # Open access point (no password)
        ap.config(essid=essid, authmode=network.AUTH_OPEN)
    
    print("Access Point started with IP:", ap.ifconfig()[0])
    sync_time()

def connect_wifi(wait = True):
    with open("wifi.txt", "r") as file:
        ssid = file.readline().strip()
        password = file.readline().strip()
    wlan.active(True)
    wlan.connect(ssid, password)

    if wait:
        for i in range(10):
            if wlan.isconnected():
                break
            time.sleep(1)
        if wlan.isconnected():
            print("Connected to", wlan.config('ssid'), "with IP", wlan.ifconfig()[0])
            sync_time()
        else:
            print("Failed to connect to", ssid)

def start_webserver(endpoints):
    def handle_request(client_socket):
        # get and decode the request
        request = parse_http_request(client_socket.recv(1024).decode())
        #print(request)
        
        # default response
        response = "HTTP/1.1 404 Not Found\n\n"

        # if the request endpoint is present in the endpoints dict
        endpoint = request['endpoint'].strip('/') if request['endpoint'] else ''
        if endpoint in endpoints:
            # execute the callback
            result = endpoints[endpoint](request)

            # if the callback executed successfully, default to 200 OK
            response = "HTTP/1.1 200 OK\nAccess-Control-Allow-Origin: *\n\n"

            # append a body to the response
            if isinstance(result, dict): # if the result is a dict, convert it to json
                response += ujson.dumps(result)
            elif result is not None: # if it's not None, convert it to a string
                response += str(result)
        
        # send the response
        client_socket.send(response)
        client_socket.close()

    def check_requests():
        # print("Checking for requests...")
        cl, addr = server_socket.accept()
        # print("Client connected from", addr)
        handle_request(cl)
        cl.close()
    
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', 80))
    server_socket.listen(5)

    print("Web server started")
    while True:
        check_requests()

def parse_http_request(http_request):
    # print(http_request)
    # Splitting the request into headers and body
    parts = http_request.split('\n\n', 1)

    # The first part is headers, the second part is body
    headers = parts[0]
    body = parts[1] if len(parts) > 1 else ''

    # Extracting each header component
    method_match = ure.search(r'^(\w+)', headers)
    endpoint_match = ure.search(r'^\w+\s+([^?\s]+)', headers)
    params_match = ure.search(r'\?([^?\s]+)\s', headers)

    # Extracting params
    params_string = params_match.group(1) if params_match else None
    params = {}
    if params_string:
        for param in params_string.split('&'):
            key, value = param.split('=')
            params[key] = value

    # store results in dict
    result = {}
    result['method'] = method_match.group(1) if method_match else None
    result['endpoint'] = endpoint_match.group(1) if endpoint_match else None
    result['params'] = params
    result['body'] = body if body != '' else None
    return result