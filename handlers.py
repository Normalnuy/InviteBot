import kb, asyncio, logging

from utils import *
from states import *

from asyncio import Future

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.types import FSInputFile

from telethon.errors import PhoneCodeInvalidError, PhoneCodeExpiredError, SessionPasswordNeededError, PhoneNumberInvalidError
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest


router = Router()


messages = {                                                          # object Message для редактирования
    "input_password": {}, # user_id
    "auth_code": {}, # user_id
    "get_file": {}, # user_id
}

events = {}

def set_bot(instance: Bot):
    global bot
    bot = instance


@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    uid = "input_password"
    get_id_message(user_id, uid)
    
    messages[uid][user_id] = await msg.answer("<b>🔰 Введите пароль для входа:</b>")
    await state.set_state(CheckPassword.password)


@router.message(CheckPassword.password)
async def check_password(msg: Message, state: FSMContext):
    await state.clear()
    
    config = get_config()
    
    user_id = msg.from_user.id
    uid = "input_password"
    uid_message = messages[uid][user_id]
    
    input_text = msg.text
    await msg.delete()

    verif = check_verif()
    
    if input_text == config['password']:
        uid_message.delete()
    
        if verif:
            await msg.answer("<b>⚜️ Вы вошли в систему!</b>", reply_markup=kb.admin_menu)
            return
    
        else:
            await msg.answer("<b>🛠 Нажмите, что верифицировать аккаунт.</b>", reply_markup=kb.verif)
            return
        
    else:
        await msg.answer("<b>❌ Доступ закрыт!</b>")
        
# ===================================================================================================================== #

@router.callback_query(F.data == 'verif')
async def start_session(clbck: CallbackQuery, state: FSMContext):
    config = get_config()
    
    user_id = clbck.from_user.id
    uid = 'auth_code'
    get_id_message(user_id, uid)
    
    future_code = Future()
    future_pass = Future()
    events[user_id] = future_code
    events[user_id + 1] = future_pass

    asyncio.create_task(
        create_session(
            config['api_id'],
            config['api_hash'],
            config['phone'],
            future_code,
            future_pass,
            user_id
        ))
    
    messages[uid][user_id] = await clbck.message.answer("⚙️ <b>На аккаунт пришел код!</b>\nВведите его ниже:")
    await state.set_state(AccountCode.account_code)


@router.message(AccountCode.account_code)
async def generate_code(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    uid = 'auth_code'
    uid_message = messages[uid][user_id]
    
    await state.update_data(account_code=msg.text)
    await msg.delete()
    data = await state.get_data()
    await state.clear()
    
    ok = await process_create(msg=msg, data=data)

    if ok:
        await uid_message.delete()
        await msg.answer(f"<b>✅ Аккаунт успешно авторизирован!</b>\nНе забудьте разрешить вход новому устройству! <b>| Настройки -> Устройства.</b>", reply_markup=kb.admin_menu)


async def create_session(api_id, api_hash, phone, future_code, future_pass, user_id):
    config = get_config()
    
    uid = 'auth_code'
    proxy = config['proxy']
    valid = await check_proxy(proxy)
    
    client = TelegramClient(f'sessions/client', api_id, api_hash, proxy=valid)
    await client.connect()

    if not await client.is_user_authorized():
        try:
            uid_message = messages[uid][user_id]
            
            session = await client.send_code_request(phone)
            code = await asyncio.wait_for(future_code, timeout=300)
            password = await asyncio.wait_for(future_pass, timeout=300)
            
            try:
                await client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=session.phone_code_hash
                )
            except PhoneCodeInvalidError:
                await uid_message.edit_text("❗️ <b>Произошла ошибка</b>\nКод не корректный.")
            except PhoneCodeExpiredError:
                await uid_message.edit_text("❗️ <b>Произошла ошибка</b>\nАвторизация основных аккаунтов не допускается. Telegram заблокировал вход.")
            except SessionPasswordNeededError:
                await client.sign_in(password=password)
        
        except PhoneNumberInvalidError:
            await uid_message.edit_text("❗️ <b>Произошла ошибка</b>\nНомер введен не правильно.")
        except Exception as e:
            logging.error(f"Failed to sign in: {e}")
            await uid_message.edit_text("❗️ <b>Произошла ошибка</b>\nУбедитесь, что ввёли правильные данные аккаунта.")
        
        await client.disconnect()
        return

async def process_create(msg: Message, data: dict):
    config = get_config()
    
    user_id = msg.from_user.id
    uid = 'auth_code'
    uid_message = messages[uid][user_id]

    code = data['account_code']
    password = False
    
    if config['account_password'] not in '0':
        password = config['account_password']

    future_code = events.get(user_id)
    future_pass = events.get(user_id + 1)

    if future_code and future_pass:
        future_code.set_result(code)
        del events[user_id]
        future_pass.set_result(password)
        del events[user_id + 1]
    else:
        await uid_message.edit_text("❌ <b>Ошибка:</b> событие не найдено.")
        return

    await asyncio.sleep(3)
    if "Произошла ошибка" not in uid_message.text:
        return True
    
    return False

# ===================================================================================================================== #

@router.message(F.text.lower() == "💬 отправить список чатов")
async def get_chats_start(msg: Message, state: FSMContext):
    await msg.delete()
    
    if msg.from_user.id not in messages['get_file']:
        messages['get_file'][msg.from_user.id] = {}
        
    messages['get_file'][msg.from_user.id] = await msg.answer("<b>✒️ Отправьте файл с расширением .txt:</b>")
    await state.set_state(GetFile.file)


@router.message(GetFile.file)
async def manage_file(msg: Message, state: FSMContext):
    await state.clear()
    
    file_id = msg.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    await msg.delete()
    message = messages['get_file'][msg.from_user.id]

    await bot.download_file(file_path, chats_file)
    result = await process_file(chats_file)

    if result:
        await message.edit_text(f"<b>✅ Список чатов успешно загружен.</b>")
    else:
        await message.edit_text(f"❗️ <b>Ошибка!</b>\nНе удалось сохранить файл.")
    return

# ===================================================================================================================== #

@router.message(F.text.lower() == "👾 проверить прокси")
async def valid_proxy(msg: Message, state: FSMContext):
    await msg.delete()
    config = get_config()
    
    proxy = config['proxy']
    valid = await check_proxy(proxy)
    
    if valid:
        await msg.answer("<b>✅ Прокси работает стабильно!</b>")
    else:
        await msg.answer("<b>❌ Прокси не работает либо не добавлен в config!</b>")
        
# ===================================================================================================================== #

@router.message(F.text.lower() == "❇️ запустить")
async def start_subscribe(msg: Message, state: FSMContext):
    await msg.delete()
    
    config = get_config()
    
    api_id = config['api_id']
    api_hash = config['api_hash']
    proxy = config['proxy']
    valid = await check_proxy(proxy)

    valid = None if "<class 'coroutine'>" in str(type(valid)) else valid
    
    try:
        
        client = TelegramClient(f'sessions/client', api_id, api_hash, proxy=valid)
        await client.connect()
        
        if not await client.is_user_authorized():
            await msg.answer("<b>❗️Аккаунт не авторизован!</b>\nУдалите client.session и пройдите верификацию заново.")
            await client.disconnect()
            return
        
        logging.info("Аккаунт верифицирован и активен.\nНачинаем подписываться...")
        
        accept = 0
        denied = 0
        
        denied_links = []
        
        chats = await process_file(chats_file)
        for chat in chats:
    
            try:
    
                if "/+" in chat:
                    hash = chat.split("https://t.me/+")[1]
                    updates = await client(ImportChatInviteRequest(hash))
                else:
                    entity = await client.get_entity(chat)
                    updates = await client(JoinChannelRequest(channel=entity))
            
                    message = await client.get_messages(entity, limit=1)
                
                    user_id = message[0].sender_id
                    user = await client.get_entity(user_id)
                
                    if user.is_bot:
                        denied_links.append(chat)
                        denied += 1
                        continue
                
                accept += 1
                    
            except:
                
                denied_links.append(chat)
                denied += 1
                
            # КД между инвайтами
            await asyncio.sleep(int(config['kd']))
        
        await client.disconnect()
        
        text = f"<b>🛠 Выполнено!</b>\n\n" \
               f"<b>✅ Подписались успешно:</b> {accept}.\n" \
               f"<b>❌ Неудачно:</b> {denied}."
        await msg.answer(text)
        
        if denied_links:
            await send_file(msg, denied_links)
        
        
    except Exception as e:
        logging.info(f"======================================================\n{e}")

# ===================================================================================================================== #

def get_id_message(user_id, uid):
    if user_id not in messages[uid]:
        messages[uid][user_id] = {}
        

async def send_file(msg: Message, denied_links: list):
    text_file = '\n'.join(denied_links)
    
    with open(denied_file, 'w') as f:
        f.write(text_file)
    
    file = FSInputFile(denied_file, filename="denied_links.txt")
    await msg.answer_document(file)
    
