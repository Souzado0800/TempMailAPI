import requests
import random
import string
import time
import re

BASE_URL = "https://api.mail.tm"

# =========================
# GERAR EMAIL ALEATÓRIO
# =========================

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# =========================
# PEGAR DOMÍNIO DISPONÍVEL
# =========================

def get_domain():
    response = requests.get(f"{BASE_URL}/domains")

    data = response.json()

    return data["hydra:member"][0]["domain"]

# =========================
# CRIAR CONTA
# =========================

def create_account():
    domain = get_domain()

    username = random_string()

    email = f"{username}@{domain}"

    password = random_string(12)

    payload = {
        "address": email,
        "password": password
    }

    response = requests.post(
        f"{BASE_URL}/accounts",
        json=payload
    )

    if response.status_code != 201:
        print("Erro ao criar conta")
        print(response.text)
        return None

    return email, password

# =========================
# LOGIN
# =========================

def login(email, password):
    payload = {
        "address": email,
        "password": password
    }

    response = requests.post(
        f"{BASE_URL}/token",
        json=payload
    )

    if response.status_code != 200:
        print("Erro no login")
        print(response.text)
        return None

    token = response.json()["token"]

    return token

# =========================
# PEGAR MENSAGENS
# =========================

def get_messages(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/messages",
        headers=headers
    )

    if response.status_code != 200:
        return []

    return response.json()["hydra:member"]

# =========================
# PEGAR CONTEÚDO DA MENSAGEM
# =========================

def get_message(token, message_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/messages/{message_id}",
        headers=headers
    )

    if response.status_code != 200:
        return None

    return response.json()

# =========================
# EXTRAIR CÓDIGO
# =========================

def extract_code(text):
    patterns = [
        r"\b\d{4,8}\b",
        r"\b[A-Z0-9]{6}\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(0)

    return None

# =========================
# MAIN
# =========================

def main():
    account = create_account()

    if not account:
        return

    email, password = account

    print("\n==============================")
    print("EMAIL TEMPORÁRIO CRIADO")
    print("==============================")
    print(f"Email: {email}")
    print(f"Senha: {password}")
    print("==============================\n")

    token = login(email, password)

    if not token:
        return

    print("Monitorando emails...\n")

    checked_messages = set()

    while True:
        try:
            messages = get_messages(token)

            for msg in messages:
                msg_id = msg["id"]

                if msg_id in checked_messages:
                    continue

                checked_messages.add(msg_id)

                full_message = get_message(token, msg_id)

                if not full_message:
                    continue

                sender = full_message["from"]["address"]
                subject = full_message.get("subject", "")
                text = full_message.get("text", "")

                full_text = f"{subject}\n{text}"

                code = extract_code(full_text)

                print("\n==============================")
                print("NOVO EMAIL RECEBIDO")
                print("==============================")
                print(f"De: {sender}")
                print(f"Assunto: {subject}")

                if code:
                    print(f"Código detectado: {code}")

                print("==============================")

            time.sleep(5)

        except KeyboardInterrupt:
            print("\nEncerrando...")
            break

        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()