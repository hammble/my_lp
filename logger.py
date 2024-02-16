from vkbottle.user import User, Message
from loguru import logger
import colored
from colored import stylize
import datetime

logger = logger
user = User("")
logger.disable('vkbottle')

@user.on.message(text='<q>')
async def logger_function(message: Message, q: str):
  user_id = message.from_id
  a = await message.get_user(user_ids=user_id)
  name = f'{a.first_name} {a.last_name}'
  current_time = datetime.datetime.now().strftime('%H:%M:%S')
  current_time = stylize(current_time, colored.fg("cyan"))
  name = stylize(name, colored.fg("red"))
  q = stylize(q, colored.fg("cyan"))
  print(f'[{current_time}] | [{name}] | [{q}]')

user.run_forever()