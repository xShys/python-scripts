import socket
import ssl
import json
from urllib.parse import urlparse
from contextlib import closing

# Funzione per leggere la risposta dal socket e stampare il contenuto ricevuto
def read_response(sock: socket.socket):
    print("[>] Richiesta inviata, in attesa di risposta...\n")
    response = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        print("[!] Timeout durante la lettura della risposta.")
        print("\n\n\n")
        print("Riavvio il programma...")
        print("\n\n\n")
        main()

    print(f"[<] Risposta ricevuta ({len(response)} bytes):\n")
    print(response.decode(errors='ignore'))

# Funzione per analizzare il socket e stampare informazioni sulla connessione
def analyze_socket_connection(sock: socket.socket):
    try:
        local_ip, local_port = sock.getsockname()
        remote_ip, remote_port = sock.getpeername()
        print(f"[✓] Connessione stabilita.")
        print(f"    - Locale: {local_ip}:{local_port}")
        print(f"    - Remoto: {remote_ip}:{remote_port}")
        print(f"    - Tipo: {'TLS su TCP' if isinstance(sock, ssl.SSLSocket) else 'TCP'}")
    except socket.error as e:
        print(f"[!] Errore durante l'analisi del socket: {e}")
        print("\n\n\n")
        print("Riavvio il programma...")
        print("\n\n\n")
        main()

# Funzione per creare una richiesta HTTP o HTTPS
def create_http_request(method: str, host: str, path: str, body: str = None, headers: dict = None) -> bytes:
    if not path:
        path = "/"

    method = method.upper()
    headers = headers or {}
    request_lines = [f"{method} {path} HTTP/1.1", f"Host: {host}", "Connection: close"]

    for key, value in headers.items():
        request_lines.append(f"{key}: {value}")

    if body:
        request_lines.append(f"Content-Length: {len(body.encode())}")
        if 'Content-Type' not in {k.lower() for k in headers or {}}:
            request_lines.append("Content-Type: application/json")
        request = "\r\n".join(request_lines) + "\r\n\r\n" + body
    else:
        request = "\r\n".join(request_lines) + "\r\n\r\n"

    return request.encode()

# Funzione per comunicare con un URL specificato e inviare una richiesta HTTP o HTTPS
def communicate_with_url(url: str, method="GET", body=None):
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme
    host = parsed_url.hostname
    path = parsed_url.path or "/"
    port = parsed_url.port

    if not host:
        print("[x] URL non valido.")
        print("\n\n\n")
        print("Riavvio il programma...")
        print("\n\n\n")
        main()
    
    if not port:
        port = 443 if scheme == "https" else 80

    headers = {
        "User-Agent": "Python-Socket-Client/1.0"
    }

    request = create_http_request(method, host, path, body, headers)

    try:
        raw_sock = socket.create_connection((host, port))
    except socket.gaierror as e:
        print(f"[x] Errore di risoluzione DNS: {e}")
        print("\n\n\n")
        print("Riavvio il programma...")
        print("\n\n\n")
        main()
    except Exception as e:
        print(f"[x] Errore di connessione, impossibile connettersi a {host}:{port} -> {e}")
        print("\n\n\n")
        print("Riavvio il programma...")
        print("\n\n\n")
        main()
    
    with closing(raw_sock):
        if scheme == "https":
            context = ssl.create_default_context()
            
            with context.wrap_socket(raw_sock, server_hostname=host) as ssl_sock:
                analyze_socket_connection(ssl_sock)
                ssl_sock.sendall(request)
                read_response(ssl_sock)
        else:
            analyze_socket_connection(raw_sock)
            raw_sock.sendall(request)
            read_response(raw_sock)

        exit = input("Premi invio per continuare o 'exit' per uscire:\t").strip().lower()
        if exit == 'exit':
            print("\n")
            print("[!] Esco dal programma.")
            return
        
        print("\n")
        main()

#Funzione principale che avvia il programma
def main():
    URL = 'https://jsonplaceholder.typicode.com/todos/1'
    METHOD = 'GET'
    BODY = None

    is_test = input("Inserire un target specifico? y/n\t exit per uscire:\t").strip().lower()

    if is_test == 'exit':
        print("[!] Esco dal programma.")
        return

    if is_test.lower() == 'n':
        print("[!] Eseguo un test su URL di esempio: https://jsonplaceholder.typicode.com/todos/1 ...\n\n")
        communicate_with_url(URL, method=METHOD, body=BODY)
    else:
        URL = input("Inserisci un URL HTTP o HTTPS:\n").strip()
        METHOD = input("Inserisci il metodo HTTP (GET, POST, PUT, DELETE) oppure premi invio per GET di default:\n").strip().upper() or "GET"
        BODY = None

        if METHOD in ["POST", "PUT", "PATCH"]:
            BODY = input("Inserisci il corpo della richiesta (JSON) oppure lascia vuoto se non serve:\n").strip()
            try:
                json.loads(BODY)

                if not BODY:
                    BODY = json.dumps({"default": "value"})

            except json.JSONDecodeError:
                print("[!] Body non valido, deve essere un JSON.")
                main()

        communicate_with_url(URL, method=METHOD, body=BODY)

# Esegue la funzione principale quando il file viene eseguito direttamente
if __name__ == "__main__":
    main()