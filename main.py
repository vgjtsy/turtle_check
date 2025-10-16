import requests
import time
import json
from urllib.parse import quote



DELAY_SECONDS = 0.1 # задержка между кошельками в секундах

USE_PROXIES = True



def read_evm_addresses(filepath):
    addresses = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                address = line.strip()
                if address:
                    addresses.append(address)
    except FileNotFoundError:
        print(f"Файл не найден: {filepath}")
    return addresses

def read_proxies(filepath):
    proxies = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                proxy = line.strip()
                if proxy:
                    if not proxy.startswith('http'):
                        proxy = f"http://{proxy}"
                    proxies.append({'http': proxy, 'https': proxy})
    except FileNotFoundError:
        print(f"Файл не найден: {filepath}")
    return proxies

def get_next_proxy(proxies, index):
    if not proxies:
        return None
    return proxies[index % len(proxies)]

def build_api_url(address):
    base_url = "https://api.turtle.xyz/turtle/airdrop/claims?wallet_addresses="
    return f"{base_url}{address}"

def fetch_eligibility_data(url, proxy=None):
    try:
        response = requests.get(url, proxies=proxy, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка API: {e}")
        return None

def parse_eligibility_response(json_data):
    is_eligible = False
    amount = 0.0
    category = "N/A"
    if json_data is None:
        return is_eligible, amount, category
    try:
        if "claims" in json_data and len(json_data["claims"]) > 0:
            claim_data = json_data["claims"][0]
            is_eligible = claim_data.get("is_eligible", False)
            if is_eligible:
                if "details" in claim_data and "total" in claim_data["details"]:
                    amount = float(claim_data["details"]["total"])
                if "details" in claim_data and "breakdown" in claim_data["details"] and len(claim_data["details"]["breakdown"]) > 0:
                    category = claim_data["details"]["breakdown"][0].get("category", "N/A")
    except (KeyError, TypeError, ValueError) as e:
        print(f"Ошибка при разборе ответа API: {e}")
        pass
    return is_eligible, amount, category

if __name__ == "__main__":
    addresses = read_evm_addresses("evm.txt")
    proxies = []
    
    if USE_PROXIES:
        proxies = read_proxies("proxies.txt")
        if proxies:
            print(f"Загружено {len(proxies)} прокси")
        else:
            print("Прокси не загружены, использую прямое подключение")

    total_tokens = 0.0
    
    with open("result.txt", 'w') as result_f:
        if addresses:
            print(f"Начинаю проверку {len(addresses)} адресов...")
            result_f.write(f"Начинаю проверку {len(addresses)} адресов...\n")

            for i, addr in enumerate(addresses):
                if i > 0:
                    time.sleep(DELAY_SECONDS)
                
                proxy = get_next_proxy(proxies, i) if USE_PROXIES else None
                
                url = build_api_url(addr)
                json_data = fetch_eligibility_data(url, proxy)
                is_eligible, amount, category = parse_eligibility_response(json_data) if json_data else (False, 0.0, "N/A")

                output_line = ""
                if is_eligible:
                    output_line = f"{i+1}/{len(addresses)}: {addr} - Eligible - {amount:.4f} ({category})"
                    total_tokens += amount
                else:
                    output_line = f"{i+1}/{len(addresses)}: {addr} - Not Eligible"
                
                print(output_line)
                result_f.write(output_line + '\n')
            
            final_summary = f"\nВсего токенов: {total_tokens:.4f}"
            print(final_summary)
            result_f.write(final_summary + '\n')
        else:
            no_addresses_msg = "Нет адресов в evm.txt."
            print(no_addresses_msg)
            result_f.write(no_addresses_msg + '\n')
