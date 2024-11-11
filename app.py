from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
import os
import json
from propriedades import *
from time import sleep

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def obter_todos_os_cards():
    url = f"https://api.notion.com/v1/databases/{os.getenv('DATABASE_ID')}/query"
    payload = {}
    todos_os_cards = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            payload['start_cursor'] = next_cursor
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        todos_os_cards.extend(data['results'])
        has_more = data['has_more']
        next_cursor = data.get('next_cursor')

    return todos_os_cards

def monitorar_novos_cards(ids_atuais):
    cards_novos = obter_todos_os_cards()
    ids_novos = set()
    with open("arquivo.txt","w") as arq:
            arq.write(json.dumps(cards_atuais))

    for card in cards_novos:
        ids_novos.add(card['id'])

        if card['id'] not in ids_atuais:
            atualizar_propriedade_ultimo_comentario(card['id'], card['created_time'])

    return ids_novos



if __name__== '__main__':
    ids_atuais = set()
    cards_atuais = obter_todos_os_cards()
    adicionar_propriedade_ultimo_comentario_ao_banco_de_dados()

    for card in cards_atuais:
        atualizar_propriedade_ultimo_comentario(card['id'], card['created_time'])
        ids_atuais.add(card['id'])


    while True:
        ids_atuais = monitorar_novos_cards(ids_atuais)
        sleep(30)





    


    


