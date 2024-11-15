import requests
import os
from dotenv import load_dotenv
import datetime
import pytz
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
fuso_horario_local = pytz.timezone('America/Sao_Paulo')

headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def listar_propriedades_do_banco_de_dados():
    url = f"https://api.notion.com/v1/databases/{os.getenv('DATABASE_ID')}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        propriedades = data['properties']
        
        print("Propriedades no banco de dados:")
        for nome, detalhes in propriedades.items():
            tipo = detalhes['type']
            print(f"- {nome}: {tipo}")
    else:
        print(f"Falha ao obter propriedades. Status Code: {response.status_code}")
        print(f"Detalhes: {response.text}")

def adicionar_propriedade_ultimo_contato_ao_banco_de_dados():
    url = f"https://api.notion.com/v1/databases/{os.getenv('DATABASE_ID')}"
    payload = {
        "properties": {
            "Último contato": {
                "date": {}
            }
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Propriedade 'Último contato' adicionada com sucesso ao banco de dados!")
    else:
        print(f"Falha ao adicionar a propriedade. Status Code: {response.status_code}")
        print(f"Detalhes: {response.text}")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def atualizar_propriedade_ultimo_contato(card_id, valor, card_name):
    valor_utc = datetime.datetime.fromisoformat(valor.replace("Z", "+00:00")).astimezone(pytz.utc)
    
    # Converte para o fuso horário local
    valor_local = valor_utc.astimezone(fuso_horario_local)
    
    # Formata para ISO 8601 com informação de fuso horário
    valor_local_iso = valor_local.strftime('%Y-%m-%dT%H:%M:%S%z')
    url = f"https://api.notion.com/v1/pages/{card_id}"

    payload = {
        "properties": {
            "Último contato": {
                "date": {
                    "start": valor_local_iso
                }
            }
        }
    }
   
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Card {card_name}: Propriedade 'Último contato' atualizada com sucesso no card!")
    else:
        print(f"Falha ao atualizar a propriedade. Status Code: {response.status_code}")
        print(f"Detalhes: {response.text}")

