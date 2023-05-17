
import os
from dotenv import load_dotenv
import time
import requests
from bs4 import BeautifulSoup as bs
from telethon import TelegramClient

load_dotenv()

tg_api_id = os.environ.get('TG_API_ID')
tg_api_hash = os.environ.get('TG_API_HASH')
tg_bot_token = os.environ.get('TG_BOT_TOKEN')
tg_chat_id = os.environ.get('TG_CHAT_ID')
miel_username = os.environ.get('MIEL_USERNAME')
miel_password = os.environ.get('MIEL_PASSWORD')
execution_interval = os.environ.get('EXECUTION_INTERVAL')

headers = {}
cookies = {}
messages = {}
login_count = 0
messages_count = 0
last_login_time = 0

login_url = "https://miel.unlam.edu.ar/principal/event/login/"
land_page_url = 'https://miel.unlam.edu.ar/principal/interno/'
inbox_url = 'https://miel.unlam.edu.ar/principal/interno/mensajes/'
login_data = {'usuario': miel_username, 'clave': miel_password}

session = requests.session()
tg_bot = TelegramClient('tg_bot', int(tg_api_id), tg_api_hash).start(bot_token=tg_bot_token)

async def send_tg_message(message):
  await tg_bot.send_message(int(tg_chat_id), message)

### MIEL LOGIN
def login():
  global cookies, last_login_time, login_count, headers

  try:
    login_response = session.post(login_url, data=login_data)
    login_count += 1

    last_login_time = time.time()
    print("Login nro. " + str(login_count) + " - " + time.strftime("%b %d, %H:%M:%S"))

    php_session_id = login_response.cookies['PHPSESSID']
    session_id = login_response.cookies['SESSID']

    if php_session_id:
      headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'Cookie': 'PHPSESSID=' + php_session_id + '; SESSID=' + session_id
      }

      print("Session ID nro. " + str(login_count) + ": " + php_session_id)

  except KeyError:
    print("Session ID vacío")

login()

while True:
  current_messages_count = 0

  ### LAND PAGE REQUEST
  try:
    land_response = session.get(land_page_url, headers=headers)
    land_soup = bs(land_response.content, "html.parser")
  except:
    login()
    continue

  ### LAND PAGE SCRAPING
  for message_tag in land_soup.find_all('div', string='Mensajes'):
    if (message_tag.find_next_sibling(class_='w3-badge w3-red w3-small')):

      inbox_url = message_tag.parent['href']

      ### INBOX REQUEST
      inbox_response = session.get(inbox_url, headers=headers)
      inbox_soup = bs(inbox_response.content, "html.parser")

      ### INBOX SCRAPING
      unread_messages = inbox_soup.find_all('tr', class_='mensaje-no-leido')
      current_messages_count += len(unread_messages)

      for msg in unread_messages:
          msg_from = msg.find_all('td')[1].text
          msg_subject = msg.find_all('td')[3].a.text.strip()
          messages.update({msg_from: msg_subject})

  if current_messages_count > messages_count:
    if len(messages) == 1:
      output = "**HAY 1 MENSAJE NUEVO EN MIeL!**\n\n"
    else:
      output = "**HAY {} MENSAJES NUEVOS EN MIeL!**\n\n".format(len(messages))

    for i, (msg_from, msg_subject) in enumerate(messages.items()):
      if i == len(messages) - 1:
        output += "• {}: __{}__".format(msg_from, msg_subject)
      else:
        output += "• {}: __{}__\n\n".format(msg_from, msg_subject)

    messages_count = current_messages_count

    print(output)

    with tg_bot:
      tg_bot.loop.run_until_complete(send_tg_message(output))
  else:
    print("No hay mensajes nuevos en MIeL - " + time.strftime("%b %d, %H:%M:%S"))

  if current_messages_count < messages_count:
    messages_count = current_messages_count

  messages = {}

  time.sleep(int(execution_interval))
