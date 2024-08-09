import os, json, requests, python_socks


current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "config.json")
chats_file = os.path.join(current_dir, "chats\\chats.txt")
denied_file = os.path.join(current_dir, "chats\\denied.txt")

def get_config():
    with open(config_path, "r") as f:
        file = f.read()
        return json.loads(file)


def check_verif():
    if os.path.exists(f"sessions\\client.session"):
        return True
    else:
        return False


async def process_file(file_path):
    
    try:
        
        with open(file_path, 'r') as f:
            text = f.read()
            chats = text.split('\n')
            return chats
        
    except Exception:
        return False


async def check_proxy(proxy):
    
    if proxy != 'proxy':
        full_proxy = proxy.split("@")
        login_pass = full_proxy[0].split(":")
        ip_port = full_proxy[1].split(":")
        
        login = login_pass[0]
        password = login_pass[1]
        ip = ip_port[0]
        port = ip_port[1]
        
        proxies = {
            'http': f"http://{login}:{password}@{ip}:{port}",
            'https': f"http://{login}:{password}@{ip}:{port}"
        }

        try:
            
            response = requests.get("http://www.google.com", proxies=proxies)

            if response.status_code == 200:
                prox = [(python_socks.ProxyType.HTTP, ip, int(port), True, login, password), True]
                return prox
        
        except Exception:
            pass
        
        return None
        
    else:
        return None
