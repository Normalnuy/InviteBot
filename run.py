import asyncio, logging
from utils import *
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router, set_bot

async def main():
    
    config = get_config()
    
    global bot, dp
    bot = Bot(token=config['token'], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)
    set_bot(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    tasks = [dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())]
    await asyncio.gather(*tasks)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
