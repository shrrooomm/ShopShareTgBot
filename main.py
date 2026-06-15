from aiogram import Bot, Dispatcher
from handlers import user
import database as db

#Основная функция
async def main():
    await db.db_start()
    bot = Bot(token = '8963087783:AAF6QypBJg5xae7WxWNHHsADryI6Krbe_KI')
    dispatcher = Dispatcher()
    dispatcher.include_router(user)
    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
