import requests
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

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

def adicionar_propriedade_ultimo_comentario_ao_banco_de_dados():
    url = f"https://api.notion.com/v1/databases/{os.getenv('DATABASE_ID')}"
    payload = {
        "properties": {
            "Último comentário": {
                "date": {}
            }
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Propriedade 'Último comentário' adicionada com sucesso ao banco de dados!")
    else:
        print(f"Falha ao adicionar a propriedade. Status Code: {response.status_code}")
        print(f"Detalhes: {response.text}")


def atualizar_propriedade_ultimo_comentario(card_id, valor):
    url = f"https://api.notion.com/v1/pages/{card_id}"
    payload = {
        "properties": {
            "Último comentário": {
                "date": {
                    "start": valor
                }
            }
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Propriedade 'Último comentário' atualizada com sucesso no card!")
    else:
        print(f"Falha ao atualizar a propriedade. Status Code: {response.status_code}")
        print(f"Detalhes: {response.text}")

