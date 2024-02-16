import requests
import vk_api
import time
import datetime
import asyncio
import re
import aiohttp
from vkbottle.user import User, Message
from vkbottle.bot import Bot, Message
from vkbottle.api import API
from collections import OrderedDict
from bs4 import BeautifulSoup
import asyncio
import os
import json
import pyowm
import random
from pyowm import OWM
from loguru import logger
import colored
from colored import stylize

owm = pyowm.OWM('ТОКЕН open weather api')
mgr = owm.weather_manager()
api = API('ТОКЕН')
token = 'ТОКЕН'
user = User('ТОКЕН')
bot = Bot('ТОКЕН')
TEMPLATES_FILE = 'temps.json'
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
timers = {}
ignored_users = {}
timer_counter = 0
owners = [] # YOUR USER ID
dov = []
prefixes = [''] # PREFIXES
logger.disable('vkbottle') #Выключает мусор с консоли

status_translation = {
    'clear sky': 'ясное небо',
    'few clouds': 'небольшая облачность',
    'scattered clouds': 'рассеянные облака',
    'broken clouds': 'облачно с прояснениями',
    'overcast clouds': 'пасмурно',
    'shower rain': 'ливень',
    'rain': 'дождь',
    'thunderstorm': 'гроза',
    'snow': 'снег',
    'light snow': 'небольшой снег',  
    'mist': 'туман'
}

status_emojis = {
    'ясное небо': '☀️',
    'небольшая облачность': '🌤️',
    'рассеянные облака': '⛅',
    'облачно с прояснениями': '🌥️',
    'пасмурно': '☁️',
    'ливень': '🌧️',
    'дождь': '🌧️',
    'гроза': '⛈️',
    'снег': '❄️',
    'небольшой снег': '🌨️',  
    'туман': '🌫️'
}

DD_SCRIPT = (
    'var i = 0;var msg_ids = [];var count = %d;'
    'var items = API.messages.getHistory({"peer_id":%d,"count":"200", "offset":"0"}).items;'
    'while (count > 0 && i < items.length) {if (items[i].out == 1) {if (items[i].id == %d) {'
    'if (items[i].reply_message) {msg_ids.push(items[i].id);msg_ids.push(items[i].reply_message.id);'
    'count = 0;};if (items[i].fwd_messages) {msg_ids.push(items[i].id);var j = 0;while (j < '
    'items[i].fwd_messages.length) {msg_ids.push(items[i].fwd_messages[j].id);j = j + 1;};count = 0;};};'
    'msg_ids.push(items[i].id);count = count - 1;};if ((%d - items[i].date) > 86400) {count = 0;};i = i + 1;};'
    'API.messages.delete({"message_ids": msg_ids,"delete_for_all":"1"});return count;'
)

if not os.path.exists(TEMPLATES_FILE):
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump({}, f)

async def edit_message(message: Message,text: str = '',att: str = ''):
    return await message.ctx_api.messages.edit(peer_id=message.peer_id, message=text,message_id=message.id, keep_forward_messages=True,keep_snippets=True,dont_parse_links=False,attachment=att)

def get_user_id_by_domain(user_domain: str):
    vk = vk_api.VkApi(token=token)
    obj = vk.method('utils.resolveScreenName', {"screen_name": user_domain})
    if isinstance(obj, list):
        return
    if obj['type'] == 'user':
        return obj["object_id"]

async def send_text_after_period(message: Message, period_seconds: int, text: str):
    await asyncio.sleep(period_seconds)
    await message.answer(text)

def get_user_id(text):
    result = []
    regex = r"(?:vk\.com\/(?P<user>[\w\.]+))|(?:\[id(?P<user_id>[\d]+)\|)"
    for user_domain, user_id in re.findall(regex, text):
        if user_domain:
            result.append(get_user_id_by_domain(user_domain))
        if user_id:
            result.append(int(user_id))
    _result = []
    for r in result:
        if r is not None:
            _result.append(r)
    return _result

async def user_id_get_mes(message: Message):
    if message.reply_message == None:
        vk_user = message.from_id
    else:
        vk_user = message.reply_message.from_id
    return vk_user

@user.on.message(text='<q>')
async def logger(message: Message, q: str):
  user_id = message.from_id
  a = await message.get_user(user_ids=user_id)
  name = f'{a.first_name} {a.last_name}'
  current_time = datetime.datetime.now().strftime('%H:%M:%S')
  current_time = stylize(current_time, colored.fg("cyan"))
  name = stylize(name, colored.fg("red"))
  q = stylize(q, colored.fg("cyan"))
  print(f'[{current_time}] | [{name}] | [{q}]')

@user.on.message(text=[f'{prefix}ид' for prefix in prefixes])
async def getid(message: Message):
  user_id = await user_id_get_mes(message)
  if message.from_id not in owners:
    print('')
    return
  await edit_message(message, f'ID [id{user_id}|Пользователя]: {user_id}')

@user.on.message(text=[f'{prefix}ид <link>' for prefix in prefixes])
async def ejdj(message: Message, link: str):
  user_id = get_user_id(link)[0]
  if message.from_id not in owners:
    print('')
    return
  await edit_message(message, f'ID [id{user_id}|Пользователя]: {user_id}')

@user.on.message(text=[f'{prefix}пинг' for prefix in prefixes])
async def ping(message: Message):
    if message.from_id not in owners:
        print('')
        return
    delta = round(time.time() - message.date, 2)
    text = f'🏓 Понг! Задержка: {delta}с.'
    await edit_message(message, text)

@user.on.message(text=[f'{prefix}+др' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    user_id = await user_id_get_mes(message=message)
    if user_id == message.from_id:
        await edit_message(message, "❌ Не добавляйте себя в друзья!")
        return
    await message.ctx_api.friends.add(user_id)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    text = f'✅ {name} добавлен в друзья.'
    await edit_message(message, text)

@user.on.message(text=[f'{prefix}+др <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    user_id = get_user_id(url)[0]
    if user_id == message.from_id:
        await edit_message(message, "❌ Не добавляйте себя в друзья!")
        return
    await message.ctx_api.friends.add(user_id)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    text = f'✅ {name} добавлен в друзья.'
    await edit_message(message, text)

@user.on.message(text=[f'{prefix}-др' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    user_id = await user_id_get_mes(message=message)
    if user_id == message.from_id:
        await edit_message(message, "❌ Не удаляйте себя из друзей!")
        return
    await message.ctx_api.friends.delete(user_id)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    text = f'✅ {name} удалён из друзей.'
    await edit_message(message, text)

@user.on.message(text=[f'{prefix}-др <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    user_id = get_user_id(url)[0]
    if user_id == message.from_id:
        await edit_message(message, "❌ Не удаляйте себя из друзей!")
        return
    await message.ctx_api.friends.delete(user_id)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    text = f'✅ {name} удалён из друзей.'
    await edit_message(message, text)

@user.on.message(text=[f'{prefix}добавить' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = await user_id_get_mes(message)
        if user_id == message.from_id:
            await edit_message(message, "❌ Не добавляйте себя в чат!")
            return
        await message.ctx_api.request("messages.addChatUser", {"user_id": user_id,"chat_id": message.peer_id - 2000000000})
        text = '✅ Добавлен в чат.'
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f"Ошибка: {ex}")

@user.on.message(text=[f'{prefix}добавить <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = get_user_id(url)[0]
        if user_id == message.from_id:
            await edit_message(message, "❌ Не добавляйте себя в чат!")
            return
        await message.ctx_api.request("messages.addChatUser", {"user_id": user_id,"chat_id": message.peer_id - 2000000000})
        text = '✅ Добавлен в чат.'
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f"Ошибка: {ex}")

@user.on.message(text=[f'{prefix}+админ' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = await user_id_get_mes(message)
        if user_id == message.from_id:
            await edit_message(message, "❌ Не добавляйте себя в админы!")
            return
        await message.ctx_api.request("messages.setMemberRole",
                                      {"peer_id": message.peer_id, "member_id": user_id, "role": "admin"})
        text = f"✅ [id{user_id}|Права администратора выданы.]"
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f'Ошибка: {ex}')

@user.on.message(text=[f'{prefix}+админ <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = get_user_id(url)[0]
        if user_id == message.from_id:
            await edit_message(message, "❌ Не добавляйте себя в админы!")
            return
        await message.ctx_api.request("messages.setMemberRole",
                                      {"peer_id": message.peer_id, "member_id": user_id, "role": "admin"})
        text = f"✅ [id{user_id}|Права администратора выданы.]"
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f'Ошибка: {ex}')

@user.on.message(text=[f'{prefix}-админ' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = await user_id_get_mes(message)
        if user_id == message.from_id:
            await edit_message(message, "❌ Не удаляйте себя из админов!")
            return
        await message.ctx_api.request("messages.setMemberRole",
                                      {"peer_id": message.peer_id, "member_id": user_id, "role": "member"})
        text = f"✅ С [id{user_id}|Права администратора сняты.]"
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f"Ошибка: {ex}")

@user.on.message(text=[f'{prefix}-админ <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = get_user_id(url)[0]
        if user_id == message.from_id:
            await edit_message(message, "❌ Не удаляйте себя из админов!")
            return
        await message.ctx_api.request("messages.setMemberRole",
                                      {"peer_id": message.peer_id, "member_id": user_id, "role": "member"})
        text = f"✅ С [id{user_id}|Права администратора сняты.]"
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f"Ошибка: {ex}")

@user.on.message(text=[f'{prefix}кик' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = await user_id_get_mes(message)
        if user_id == message.from_id:
            await edit_message(message, "❌ Не кикайте себя!")
            return
        await message.ctx_api.request("messages.removeChatUser", {"member_id": user_id,
                                                                  "chat_id": message.peer_id - 2000000000})
        text = f"✅ Исключен с беседы."
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f'Ошибка: {ex}')

@user.on.message(text=[f'{prefix}кик <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    try:
        user_id = get_user_id(url)[0]
        if user_id == message.from_id:
            await edit_message(message, "❌ Не кикайте себя!")
            return
        await message.ctx_api.request("messages.removeChatUser", {"member_id": user_id,"chat_id": message.peer_id - 2000000000})
        text = f"✅ Исключен с беседы."
        await edit_message(message, text)
    except Exception as ex:
        await edit_message(message, f'Ошибка: {ex}')

@user.on.message(text=[f'{prefix}выйти' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    text = f"✅ Покинул беседу"
    await edit_message(message, text)
    await message.ctx_api.request("messages.removeChatUser", {"member_id": message.from_id,"chat_id": message.peer_id - 2000000000})

@user.on.message(text=[f'{prefix}+чс' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    user_id = await user_id_get_mes(message)
    if user_id == message.from_id:
        await edit_message(message, "❌ Не добавляйте себя в чс!")
        return
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    await message.ctx_api.account.ban(user_id)
    await edit_message(message, f'✅ {name} добавлен в ЧС')

@user.on.message(text=[f'{prefix}+чс <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    user_id = get_user_id(url)[0]
    if user_id == message.from_id:
        await edit_message(message, "❌ Не добавляйте себя в чс!")
        return
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    await message.ctx_api.account.ban(user_id)
    await edit_message(message, f'✅ {name} добавлен в ЧС')

@user.on.message(text=[f'{prefix}-чс' for prefix in prefixes])
async def greeting(message: Message):
    if message.from_id not in owners:
        print('')
        return
    user_id = await user_id_get_mes(message)
    if user_id == message.from_id:
        await edit_message(message, "❌ Не удаляйте себя из ЧС!")
        return
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    await message.ctx_api.account.unban(user_id)
    await edit_message(message, f'✅ {name} удален из ЧС')

@user.on.message(text=[f'{prefix}-чс <url>' for prefix in prefixes])
async def greeting(message: Message, url: str):
    if message.from_id not in owners:
        print('')
        return
    user_id = get_user_id(url)[0]
    if user_id == message.from_id:
        await edit_message(message, "❌ Не удаляйте себя из ЧС!")
        return
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    await message.ctx_api.account.unban(user_id)
    await edit_message(message, f'✅ {name} удален из ЧС')

@user.on.message(text=[f'{prefix}влс\n<text>' for prefix in prefixes])
async def greeting(message: Message, text: str):
    if message.from_id not in owners:
        print('')
        return
    user_id = await user_id_get_mes(message)
    print(user_id)
    await message.ctx_api.request("messages.send", {"peer_id": user_id, "message": text, "random_id": 0})
    tt = '✅ Сообщение отправлено.'
    await edit_message(message, tt)

@user.on.message(text=[f'{prefix}влс <url>\n<text>' for prefix in prefixes])
async def greeting(message: Message, url: str, text: str):
    if message.from_id not in owners:
        print('')
        return
    user_id = get_user_id(url)[0]
    print(user_id)
    await message.ctx_api.request("messages.send", {"peer_id": user_id, "message": text, "random_id": 0})
    tt = '✅ Сообщение отправлено.'
    await edit_message(message, tt)

@user.on.message(text=[f'{prefix}+шаб <name>\n<text>' for prefix in prefixes])
async def add_template(message: Message, name: str, text: str):
    if message.from_id not in owners:
        return
    else:
        with open(TEMPLATES_FILE, 'r') as f:
            templates = json.load(f)
        templates[name] = text
        with open(TEMPLATES_FILE, 'w') as f:
            json.dump(templates, f)
        await edit_message(message=message, text=f"✅ Шаблон «{name}» создан.")

@user.on.message(text=[f'{prefix}-шаб <name>' for prefix in prefixes])
async def delete_template(message: Message, name: str):
    if message.from_id not in owners:
        return
    else:
        with open(TEMPLATES_FILE, 'r') as f:
            templates = json.load(f)
        if name in templates:
            del templates[name]
            with open(TEMPLATES_FILE, 'w') as f:
                json.dump(templates, f)
            await edit_message(message=message, text=f"✅ Шаблон «{name}» удален.")
        else:
            await edit_message(message=message, text=f"❌ Шаблон «{name}» не найден.")

@user.on.message(text=[f'{prefix}~шаб <name>\n<new_text>' for prefix in prefixes])
async def edit_template(message: Message, name: str, new_text: str):
    if message.from_id not in owners:
        return
    else:
        with open(TEMPLATES_FILE, 'r') as f:
            templates = json.load(f)
        if name in templates:
            templates[name] = new_text
            with open(TEMPLATES_FILE, 'w') as f:
                json.dump(templates, f)
            await edit_message(message=message, text=f"✅ Текст шаблона «{name}» изменен.")
        else:
            await edit_message(message=message, text=f"❌ Шаблон «{name}» не найден.")

@user.on.message(text=[f'{prefix}шабы' for prefix in prefixes])
async def list_templates(message: Message):
    if message.from_id not in owners:
        return
    else:
        with open(TEMPLATES_FILE, 'r') as f:
            template_names = json.load(f, object_pairs_hook=OrderedDict)
        if template_names:
            template_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(template_names))
            await edit_message(message=message, text=f"📖 Список шаблонов:\n{template_list}")
        else:
            await edit_message(message=message, text="📖 Список шаблонов пуст.")

@user.on.message(text=[f'{prefix}шаб <name>' for prefix in prefixes])
async def use_template(message: Message, name: str):
    if message.from_id not in owners:
        return
    else:
        with open(TEMPLATES_FILE, 'r') as f:
            templates = json.load(f)

        if name in templates:
            template_text = templates[name]
            await edit_message(message=message, text=f"{template_text}")
        else:
            await edit_message(message=message, text=f"❌ Шаблон «{name}» не найден.")

@user.on.message(text=[f'{prefix}погода <city>' for prefix in prefixes])
async def weather_info(message: Message, city: str):
    if message.from_id not in owners:
        return
    observation = mgr.weather_at_place(city)
    w = observation.weather
    temperature = w.temperature('celsius')["temp"]
    wind = w.wind()["speed"]
    humidity = w.humidity
    status = w.detailed_status.lower()
    translated_status = status_translation.get(status, status)
    emoji = status_emojis.get(translated_status, '')
    response = (
        f"📝 Погода на сегодня в «{city}»:\n\n"
        f"🌡️ Температура: {temperature}°C\n"
        f"🌪️ Скорость ветра: {wind} м/с\n"
        f"🫧 Влажность: {humidity}%\n"
        f"{emoji}Статус: {translated_status}"
    )
    await edit_message(message, response)

@user.on.message(text=[f'{prefix}реши <equation>' for prefix in prefixes])
async def solve_equation(message: Message, equation: str):
    if message.from_id not in owners:
        return
    try:
        result = eval(equation)
        await edit_message(message, text=f"📝 Результат: {result}")
    except Exception as e:
        error_message = f"⚠ Произошла неизвестная ошибка."
        await edit_message(message, error_message)

@user.on.message(text=[f'{prefix}+таймер <minutes:int>\n<text>' for prefix in prefixes])
async def set_timer(message: Message, minutes: int, text: str):
    if message.from_id not in owners:
        return
    try:
        global timer_counter
        response = "⌚ Таймер установлен!"
        await edit_message(message, response)
        timer_counter += 1
        timer_id = timer_counter
        timers[timer_id] = {
            'minutes': minutes,
            'text': text,
            'user_id': message.from_id,
            'start_time': datetime.datetime.now()  # Сохраняем текущее время
        }

        await asyncio.sleep(minutes * 60)
        if timer_id in timers:
            await message.answer(text)
            timers.pop(timer_id)
        for idx, timer_info in list(timers.items()):
            if idx > timer_id:
                timers[idx - 1] = timers.pop(idx)
    except Exception as e:
        print(f"Ошибка при установке таймера: {e}")

@user.on.message(text=[f'{prefix}таймеры' for prefix in prefixes])
async def list_timers(message: Message):
    if not timers:
        await edit_message(message, text="⌚ Нет активных таймеров.")
        return
    response = "⌚ Список активных таймеров:\n"
    for timer_id, timer_info in timers.items():
        response += f"{timer_id}. {timer_info['text']} -> {timer_info['minutes']} минуток\n"
    await edit_message(message, response)

@user.on.message(text=[f'{prefix}-таймер <timer_id:int>' for prefix in prefixes])
async def remove_timer(message: Message, timer_id: int):
    if message.from_id not in owners:
        return
    global timers, timer_counter
    if timer_id in timers:
        timers.pop(timer_id)
        await edit_message(message, text=f"✅ Таймер с ID «{timer_id}» удален.")
    else:
        await edit_message(message, text=f"❌ Таймер с ID «{timer_id}» не найден.")
    for idx, timer_info in timers.items():
        if idx > timer_id:
            timers[idx - 1] = timers.pop(idx)
    if not timers:
        timer_counter = 0


@user.on.message(text=[f'{prefix}+дов' for prefix in prefixes])
async def povtoryalka(message: Message):
    if message.from_id not in owners:
        return
    user_id = await user_id_get_mes(message)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    if user_id in dov:
        await edit_message(message, f'❌ {name} уже был добавлен в список доверенных!')
    else:
        dov.append(user_id)
        await edit_message(message, f'✅ {name} добавлен в список доверенных!')

@user.on.message(text=[f'{prefix}+дов <link>' for prefix in prefixes])
async def povtoryalka(message: Message, link: str):
    if message.from_id not in owners:
        return
    user_id = get_user_id(link)[0]
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    if user_id in dov:
        await edit_message(message, f'❌ {name} уже был добавлен в список доверенных!')
    else:
        dov.append(user_id)
        await edit_message(message, f'✅ {name} добавлен в список доверенных!')

@user.on.message(text=[f'{prefix}-дов' for prefix in prefixes])
async def povtoryalka(message: Message):
    if message.from_id not in owners:
        return
    user_id = await user_id_get_mes(message)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    if user_id in dov:
        dov.remove(user_id)
        await edit_message(message, f'✅ {name} удален из списка доверенных!')
    else:
        await edit_message(message, f"❌ {name} не был в списке доверенных!")

@user.on.message(text=[f'{prefix}-дов <link>' for prefix in prefixes])
async def povtoryalka(message: Message, link: str):
    if message.from_id not in owners:
        return
    user_id = get_user_id(link)[0]
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    if user_id in dov:
        dov.remove(user_id)
        await edit_message(message, f'✅ {name} удален из списка доверенных!')
    else:
        await edit_message(message, f"❌ {name} не был в списке доверенных!")

@user.on.message(text=[f'{prefix}довы' for prefix in prefixes])
async def dovsspisok(message: Message):
    if message.from_id not in owners:
        return
    if not dov:
        await edit_message(message, '❌ Нет доверенных пользователей!')
    else:
        response = "📝 Список доверенных пользователей:\n"
        for user_id in dov:
            a = await message.get_user(user_ids=user_id)
            name = f'[id{a.id}|{a.first_name} {a.last_name}]'
            response += f"{name}\n"
        await edit_message(message, response)

@user.on.message(text=[f'{prefix}игноры' for prefix in prefixes])
async def show_ignored_users(message: Message):
    if message.from_id not in owners:
        return
    ignored_info = []
    for target_id, ignored in ignored_users.items():
        for user_id in ignored:
            user_info = await user.api.users.get(user_ids=user_id)
            user_name = f"{user_info[0].first_name} {user_info[0].last_name}"
            ignored_info.append(f"[id{user_id}|{user_name}]")

    if ignored_info:
        await edit_message(message, "📝 Список игнорируемых пользователей:\n" + "\n".join(ignored_info))
    else:
        await edit_message(message, "❌ Список игнорируемых пользователей пуст.")

@user.on.message(text=['/скажи <text>', '/Скажи <text>'])
async def dovtext(message: Message, text: str):
    if message.from_id in dov:
        await message.answer(f'{text}')
    else:
        print('')

@user.on.message(text=[f'{prefix}инфо' for prefix in prefixes])
async def infolp(message: Message):
    if message.from_id not in owners:
        return
    user_id = message.from_id
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    dov_count = len(dov)
    ignored_count = len(ignored_users)
    timers_count = len(timers)
    with open(TEMPLATES_FILE, 'r') as f:
        templates = json.load(f)
    templates_count = len(templates)
    if prefixes:
        prefixes_list = ", ".join(prefixes)
        prefixes_info = f"📖 Префиксы команд: {prefixes_list}\n"
    else:
      prefixes_info = "❌ Нет добавленных префиксов\n"
    text = [
        f'👤 Пользователь {name}\n'
        f'⚙ Префикс повторялки: /скажи\n'
        f'⚙ Префикс удалялки: Дд\n'
        f'▶ Количество доверенных: {dov_count}\n'
        f'▶ Количество игнорируемых: {ignored_count}\n'
        f'▶ Количество таймеров: {timers_count}\n'
        f'▶ Количество шаблонов: {templates_count}\n'
        f'{prefixes_info}'
    ]
    await edit_message(message, text)

@user.on.message(text=[f'{prefix}+игнор' for prefix in prefixes])
async def add_ignored_user(message: Message):
    if message.from_id not in owners:
        return
    user_id = await user_id_get_mes(message)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    target_id = message.from_id
    if user_id == target_id:
        await edit_message(message, "⚠️ Зачем ты себя в игнор-лист добавляешь, чел..")
        return
    if user_id not in ignored_users:
        ignored_users[user_id] = []
    if user_id in ignored_users[user_id]:
        await edit_message(message, f"❌ {name} уже находится в списке игнорируемых.")
    else:
        ignored_users[user_id].append(user_id)
        await edit_message(message, f"✅ {name} добавлен в список игнорируемых.")

@user.on.message(text=[f'{prefix}+игнор <link>' for prefix in prefixes])
async def add_ignored_user(message: Message, link: str):
    if message.from_id not in owners:
        return
    user_id = get_user_id(link)[0]
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    target_id = message.from_id
    if user_id == target_id:
        await edit_message(message, "⚠️ Зачем ты себя в игнор-лист добавляешь, чел..")
        return
    if user_id not in ignored_users:
        ignored_users[user_id] = []
    if user_id in ignored_users[user_id]:
        await edit_message(message, f"❌ {name} уже находится в списке игнорируемых.")
    else:
        ignored_users[user_id].append(user_id)
        await edit_message(message, f"✅ {name} добавлен в список игнорируемых.")

@user.on.message(text=[f'{prefix}-игнор' for prefix in prefixes])
async def remove_ignored_user(message: Message):
    if message.from_id not in owners:
        return
    user_id = await user_id_get_mes(message)
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    target_id = message.from_id
    if user_id == target_id:
        await edit_message(message, "⚠️ А зачем себя удалять с игнор-листа, гений?")
        return
    if user_id in ignored_users:
        ignored_users.pop(user_id)
        await edit_message(message, f"✅ {name} удален из списка игнорируемых.")
    else:
        await edit_message(message, f"❌ {name} не найден в списке игнорируемых.")

@user.on.message(text=[f'{prefix}-игнор <link>' for prefix in prefixes])
async def remove_ignored_user(message: Message, link: str):
    if message.from_id not in owners:
        return
    user_id = get_user_id(link)[0]
    a = await message.get_user(user_ids=user_id)
    name = f'[id{a.id}|{a.first_name} {a.last_name}]'
    target_id = message.from_id
    if user_id == target_id:
        await edit_message(message, "⚠️ А зачем себя удалять с игнор-листа, гений?")
        return
    if user_id in ignored_users:
        ignored_users.pop(user_id)
        await edit_message(message, f"✅ {name} удален из списка игнорируемых.")
    else:
        await edit_message(message, f"❌ {name} не найден в списке игнорируемых.")

@user.on.message(text=['дд', 'Дд <count:int>', 'Дд', 'дд <count:int>'])
async def greeting(message: Message, count: int = 2):
    if message.from_id not in owners:
        return
    ct = count + 1
    await message.ctx_api.execute(DD_SCRIPT % (ct,message.peer_id,message.from_id,int(datetime.datetime.now().timestamp())))

@user.on.message() 
async def delete_ignored_messages(message: Message):
    if message.from_id in ignored_users:
        await user.api.messages.delete(message_ids=message.id)

user.run_forever()