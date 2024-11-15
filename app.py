from dotenv import load_dotenv
import requests
from datetime import datetime, timezone
import os
import json
from propriedades import *
from time import sleep
import re
import schedule
import threading
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}
webhook_url = os.getenv('SLACK_WEBHOOK_URL')


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
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
        projeto_property = card['properties'].get('Name', {})
        title_list = projeto_property.get('title', [])

        # Verificar se a lista 'title' não está vazia
        if not title_list:
            nome = "Sem título"
        else:
            nome = card['properties']['Name']['title'][0]['text']['content']

        if card['id'] not in ids_atuais:
            atualizar_propriedade_ultimo_contato(card['id'], card['created_time'],nome)
        
        atualizar_emoji(card)

    return cards_novos, ids_novos

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def atualizar_emoji(card):
    
    ultimo_contato_data = card['properties'].get("Último contato", {}).get("date", {})
    ultimo_contato_str = ultimo_contato_data.get("start")
    
    if not ultimo_contato_str:
        print(f"[Aviso] Card {card['id']} não possui 'Último contato'. Pulando atualização do emoji.")
        return

    # Analisar a data com informação de fuso horário
    ultimo_contato = datetime.datetime.fromisoformat(ultimo_contato_str)
    
    # Obter o datetime atual no fuso horário local
    agora = datetime.datetime.now(fuso_horario_local)
    
    # Converter 'ultimo_contato' para fuso horário local se necessário
    if ultimo_contato.tzinfo is None:
        # Se a data for naive, assumir fuso horário local
        ultimo_contato = fuso_horario_local.localize(ultimo_contato)
    else:
        ultimo_contato = ultimo_contato.astimezone(fuso_horario_local)

    diferenca = agora - ultimo_contato
    diferenca_em_horas = diferenca.total_seconds() / 3600

    if diferenca_em_horas >= 2 and  diferenca_em_horas < 6:
        emoji = "🕑"
    elif diferenca_em_horas >= 6 and diferenca_em_horas< 12:
        emoji = "❄️"
    elif diferenca_em_horas >= 12 and diferenca_em_horas< 24:
        emoji = "❄️❄️"
    elif diferenca_em_horas >= 24 and diferenca_em_horas< 48:
        emoji = "🥶🥶"
    elif diferenca_em_horas >= 48:
        emoji = "🚨🥶"
    else:
        emoji = "🔥"

    projeto_property = card['properties'].get('Name', {})
    title_list = projeto_property.get('title', [])

    # Verificar se a lista 'title' não está vazia
    if not title_list:
        print(f"Card {card['id']} não possui título em 'Projeto'. Pulando atualização do emoji.")
        return
    
    nome = card['properties']['Name']['title'][0]['text']['content']
    nome_card_sem_emoji = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]', '', nome)

    payload = {
        "properties": {
            "Name": {
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

    print(f"Card {nome} atualizado com sucesso!")

def job():
    cards_atuais = obter_todos_os_cards()
    enviar_notificacao_slack(cards_atuais)

def enviar_notificacao_slack(cards):
    cardsNovos, cards2h, cards6h, cards12h, cards24h, cards48h = [], [], [], [], [], []

    for card in cards:
        projeto_property = card['properties'].get('Name', {})
        title_list = projeto_property.get('title', [])

        # Verificar se a lista 'title' não está vazia
        if not title_list:
            continue
        nome = card['properties']['Name']['title'][0]['text']['content']
        nome_card_sem_emoji = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]', '', nome)
        ultimo_contato_str = card['properties']["Último contato"]["date"]["start"]
        ultimo_contato = datetime.datetime.fromisoformat(ultimo_contato_str.replace("Z", "+00:00")).replace(tzinfo=None)
        agora = datetime.datetime.now()
        diferenca = agora - ultimo_contato
        diferenca_em_horas = diferenca.total_seconds() / 3600

        if diferenca_em_horas >= 2 and  diferenca_em_horas < 6:
            cards2h.append(nome_card_sem_emoji)
        elif diferenca_em_horas >= 6 and diferenca_em_horas< 12:
            cards6h.append(nome_card_sem_emoji)
        elif diferenca_em_horas >= 12 and diferenca_em_horas< 24:
            cards12h.append(nome_card_sem_emoji)
        elif diferenca_em_horas >= 24 and diferenca_em_horas< 48:
            cards24h.append(nome_card_sem_emoji)
        elif diferenca_em_horas >= 48 and ultimo_contato.month == agora.month:
            cards48h.append(nome_card_sem_emoji)
        elif diferenca_em_horas < 2:
            cardsNovos.append(nome_card_sem_emoji)

    def formatar_lista(lista):
        return '\n'.join(f"> {item}" for item in lista) if lista else '> Nenhum'

    data_hoje = datetime.datetime.now().strftime('%d/%m/%Y')

    mensagem = f"""
📢 *Notificação Comercial Diária - Leads Pendentes ({data_hoje})*
Bom dia, time! Aqui está o resumo dos leads que estão aguardando atualização:

>*Novas entradas: 🔥*
{formatar_lista(cardsNovos)}
>
>*Leads sem contato há 2 horas ⏰:*
{formatar_lista(cards2h)}
>
>*Leads sem contato há 6 horas ❄️:*
{formatar_lista(cards6h)}
>
>*Leads sem contato há 12 horas ❄️❄️:*
{formatar_lista(cards12h)}
>
>*Leads sem contato há 24 horas 🥶:*
{formatar_lista(cards24h)}
>
>*Leads sem contato há 48 horas 🚨:*
{formatar_lista(cards48h)}
>
>Por favor, entrem em contato com esses leads o mais rápido possível para manter o fluxo de atendimento e aumentar as chances de fechamento!
"""

    payload = {
        "text": mensagem
    }
    response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")
    elif response.status_code == 200:
        print("Mensagem enviada com sucesso!")

def obter_card_por_id(card_id):
    url = f"https://api.notion.com/v1/pages/{card_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def monitorar_novos_cards_thread(ids_atuais):
    print("---------------- Monitoramento iniciado! -------------------------")
    while True:
        monitorar_novos_cards(ids_atuais)
        sleep(30)  


def schedule_thread():
    while True:
        schedule.run_pending()
        sleep(1)



if __name__== '__main__':


    ids_atuais = set()
    adicionar_propriedade_ultimo_contato_ao_banco_de_dados()
    cards_atuais = obter_todos_os_cards()

    # with open('cards.json', 'w') as f:
    #     json.dump(cards_atuais, f, indent=4)
   

    # Faz a atribuiçao inicial do ultimo contato = created_time
    for card in cards_atuais:
        ultimo_contato = card['properties'].get("Último contato", {}).get("date")
   
        if ultimo_contato is None or ultimo_contato.get("start") is None:
            projeto_property = card['properties'].get('Name', {})
            title_list = projeto_property.get('title', [])

            # Verificar se a lista 'title' não está vazia
            if not title_list:
                nome = "Sem título"
            else:
                nome = card['properties']['Name']['title'][0]['text']['content']
            atualizar_propriedade_ultimo_contato(card['id'], card['created_time'],nome)
            # Buscar o card atualizado
            updated_card = obter_card_por_id(card['id'])
            card['properties'] = updated_card['properties']
            # Atualizar a variável 'ultimo_contato'
            ultimo_contato = card['properties']['Último contato']['date']
        ids_atuais.add(card['id'])
       

    schedule.every().day.at("08:00").do(job)

    # Inicia a thread de monitoramento
    threading.Thread(target=monitorar_novos_cards_thread, args=(ids_atuais,)).start()
    # Inicia a thread de agendamento
    threading.Thread(target=schedule_thread).start()

    





    


    


