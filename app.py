from dotenv import load_dotenv
import requests
from datetime import datetime, timezone
import os
import json
from propriedades import *
from time import sleep
import re

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
 

    for card in cards_novos:
        ids_novos.add(card['id'])

        if card['id'] not in ids_atuais:
            atualizar_propriedade_ultimo_comentario(card['id'], card['created_time'])
        
        atualizar_emoji(card)

    return cards_novos, ids_novos

def atualizar_emoji(card):
    
    ultimo_comentario_str = card['properties']["Último comentário"]["date"]["start"]
    ultimo_comentario = datetime.datetime.fromisoformat(ultimo_comentario_str.replace("Z", "+00:00")).replace(tzinfo=None)
    agora = datetime.datetime.now()
    diferenca = agora - ultimo_comentario
    diferenca_em_horas = diferenca.total_seconds() / 3600

    if diferenca_em_horas > 2 and  diferenca_em_horas < 6:
        emoji = "🕑"
    elif diferenca_em_horas > 6 and diferenca_em_horas< 12:
        emoji = "❄️"
    elif diferenca_em_horas > 12 and diferenca_em_horas< 24:
        emoji = "❄️❄️"
    elif diferenca_em_horas > 24 and diferenca_em_horas< 48:
        emoji = "🥶🥶"
    elif diferenca_em_horas > 48:
        emoji = "🚨🥶"
    else:
        emoji = "🔥"
    
    nome = card['properties']['Projeto']['title'][0]['text']['content']
    nome_card_sem_emoji = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]', '', nome)

    payload = {
        "properties": {
            "Projeto": {
                "title": [
                    {
                        "text": {
                            "content": f"{nome_card_sem_emoji.strip()} {emoji}"
                        }
                    }
                ]
            }
        }
    }

    url = f"https://api.notion.com/v1/pages/{card['id']}"
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()

    print(f"Card {card['id']} atualizado com sucesso!")

def enviar_notificacao_slack(nome_card):
    payload = {
        "text": "teste"
    }
    response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")


if __name__== '__main__':
    webhook_url = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'  # Substitua pelo seu webhook URL do Slack
    ids_atuais = set()
    cards_atuais = obter_todos_os_cards()
    # adicionar_propriedade_ultimo_comentario_ao_banco_de_dados()

    # Faz a atribuiçao inicial do ultimo comentario = created_time
    for card in cards_atuais:
        if card["properties"].get("Último comentário") is None:
            atualizar_propriedade_ultimo_comentario(card['id'], card['created_time'])
        ids_atuais.add(card['id'])
        atualizar_emoji(card)


    # Começa o monitoramento
    while True:
        # Atualiza a propriedade e o emoji para cards novos 
        cards_atuais, ids_atuais = monitorar_novos_cards(ids_atuais)

        # Enviar uma notificaçao para o slack
        # enviar_notificacao_slack(cards_atuais)

        sleep(30)





    


    


