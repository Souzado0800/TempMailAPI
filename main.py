import requests
import random
import string
import time
import re
from datetime import datetime

BASE_URL = "https://api.mail.tm"

CHECK_INTERVAL = 10

# ==========================================
# SESSION HTTP
# ==========================================

session = requests.Session()

# ==========================================
# GERAR STRING ALEATÓRIA
# ==========================================

def random_string(length=10):
    return ''.join(
        random.choices(
            string.ascii_lowercase + string.digits,
            k=length
        )
    )

# ==========================================
# PEGAR DOMÍNIO DISPONÍVEL
# ==========================================

def get_domain():
    try:
        response = session.get(
            f"{BASE_URL}/domains",
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        domains = data.get("hydra:member", [])

        if not domains:
            raise Exception("Nenhum domínio encontrado.")

        return domains[0]["domain"]

    except Exception as e:
        print(f"[ERRO] Falha ao obter domínio: {e}")
        return None

# ==========================================
# CRIAR CONTA
# ==========================================

def create_account():
    domain = get_domain()

    if not domain:
        return None

    username = random_string()

    email = f"{username}@{domain}"

    password = random_string(12)

    payload = {
        "address": email,
        "password": password
    }

    try:
        response = session.post(
            f"{BASE_URL}/accounts",
            json=payload,
            timeout=15
        )

        if response.status_code != 201:
            print("[ERRO] Falha ao criar conta")
            print(response.text)
            return None

        return email, password

    except Exception as e:
        print(f"[ERRO] Create account: {e}")
        return None

# ==========================================
# LOGIN
# ==========================================

def login(email, password):
    payload = {
        "address": email,
        "password": password
    }

    try:
        response = session.post(
            f"{BASE_URL}/token",
            json=payload,
            timeout=15
        )

        if response.status_code != 200:
            print("[ERRO] Login falhou")
            print(response.text)
            return None

        token = response.json().get("token")

        return token

    except Exception as e:
        print(f"[ERRO] Login: {e}")
        return None

# ==========================================
# HEADERS AUTH
# ==========================================

def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }

# ==========================================
# PEGAR MENSAGENS
# ==========================================

def get_messages(token):
    try:
        response = session.get(
            f"{BASE_URL}/messages",
            headers=auth_headers(token),
            timeout=15
        )

        if response.status_code != 200:
            return []

        data = response.json()

        return data.get("hydra:member", [])

    except Exception as e:
        print(f"[ERRO] Get messages: {e}")
        return []

# ==========================================
# PEGAR MENSAGEM COMPLETA
# ==========================================

def get_message(token, message_id):
    try:
        response = session.get(
            f"{BASE_URL}/messages/{message_id}",
            headers=auth_headers(token),
            timeout=15
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:
        print(f"[ERRO] Get message: {e}")
        return None

# ==========================================
# EXTRAIR CÓDIGOS
# ==========================================

def extract_code(text):
    patterns = [
        r"\b\d{4,8}\b",
        r"\b[A-Z0-9]{6}\b",
        r"\b[A-Z0-9]{8}\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(0)

    return None

# ==========================================
# EXTRAIR LINKS
# ==========================================

def extract_links(text):
    pattern = r'https?://[^\s<>"\']+'

    links = re.findall(pattern, text)

    clean_links = []

    for link in links:
        link = link.strip('">),.')

        if link not in clean_links:
            clean_links.append(link)

    return clean_links

# ==========================================
# FORMATADOR
# ==========================================

def separator():
    print("\n" + "=" * 50)

# ==========================================
# MAIN
# ==========================================

def main():
    account = create_account()

    if not account:
        return

    email, password = account

    separator()
    print("EMAIL TEMPORÁRIO CRIADO")
    separator()

    print(f"Email : {email}")
    print(f"Senha : {password}")

    separator()

    token = login(email, password)

    if not token:
        return

    print("\nMonitorando emails...\n")

    checked_messages = set()

    while True:
        try:
            messages = get_messages(token)

            for msg in messages:
                msg_id = msg.get("id")

                if not msg_id:
                    continue

                if msg_id in checked_messages:
                    continue

                checked_messages.add(msg_id)

                full_message = get_message(token, msg_id)

                if not full_message:
                    continue

                sender = (
                    full_message.get("from", {})
                    .get("address", "Desconhecido")
                )

                subject = full_message.get("subject", "")

                text = full_message.get("text", "")

                html = ""

                if full_message.get("html"):
                    html = " ".join(full_message["html"])

                full_text = f"""
                {subject}

                {text}

                {html}
                """

                code = extract_code(full_text)

                links = extract_links(full_text)

                separator()
                print("NOVO EMAIL RECEBIDO")
                separator()

                print(f"Horário : {datetime.now().strftime('%H:%M:%S')}")
                print(f"De       : {sender}")
                print(f"Assunto  : {subject}")

                if code:
                    separator()
                    print("CÓDIGO DETECTADO")
                    separator()
                    print(code)

                if links:
                    separator()
                    print("LINKS ENCONTRADOS")
                    separator()

                    for link in links:
                        print(link)

                separator()

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n[INFO] Encerrando monitoramento...")
            break

        except Exception as e:
            print(f"\n[ERRO LOOP] {e}")

            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()