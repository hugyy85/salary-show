import logging
from statistics import mean, mode, median
from urllib.parse import urljoin

from hh_connector import Hh
from graph import Graph
from config import TG_BOT_TOKEN, WEBAPP_HOST, WEBAPP_PORT, WEBAPP_ADDRESS, WEBHOOK_PATH, WEBHOOK_IP, DEBUG

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook

bot = Bot(token=TG_BOT_TOKEN)
STORAGE = MemoryStorage()
dp = Dispatcher(bot, storage=STORAGE)

if DEBUG:
    dp.middleware.setup(LoggingMiddleware())


async def on_startup(dp):
    await bot.set_webhook(urljoin(WEBAPP_ADDRESS, WEBHOOK_PATH), ip_address=WEBHOOK_IP)


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


class ShowSalaryGraph(StatesGroup):
    waiting_for_specialisation = State()


@dp.message_handler(commands=["show_salary_graph"], state='*')
async def show_salary_graph(message: types.Message):
    await message.reply("""Чтобы получить график интересующих вас зарплат, введите название *должности* или *навык*""",
                        parse_mode="Markdown")
    await ShowSalaryGraph.waiting_for_specialisation.set()
    return


@dp.message_handler(commands=["show_search_help"])
async def show_search_help(message: types.Message):
    await message.answer('''
Если ввести *врач*, то поиск зарплат будет по всей стране.
Локализировать поиск можно введя *новосибирск врач*

Если поиск идёт по языкам программирования,
то для более точного результата необходимо написать технологию а не язык,
чтобы выборка получалась более репрезентативная.

Лучше написать *django* чем *python* ''', parse_mode="Markdown")


@dp.message_handler(state=ShowSalaryGraph.waiting_for_specialisation)
async def enter_specialisation(message: types.Message, state: FSMContext):
    await message.answer(f"Необходимо немного подождать. Обычно не больше 10 секунд . . .")
    chat = message.chat
    logging.info(f'CHAT_ID:{chat.id} - {chat.full_name} - {chat.mention}. Message: {message.text} ')
    try:
        hh_obj = Hh()
        salaries = await hh_obj.get_salary_normal(message.text)
        if salaries:
            with Graph(salaries) as graph:
                await message.answer(f"График зарплат по профессии: {message.text}")
                await message.answer(f"""
Среднее значение: {round(mean(salaries)):,} р.
Мода(зарплата которая встречается чаще других): {round(mode(salaries)):,}р.
Медиана:{round(median(salaries)):,}
""")
                await STORAGE.set_data(user=message.chat.id, data=message.text)
                keyboard = types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton('Показать 10 самых высоких должностей',
                                               callback_data=f'best_salary'
                                               )
                )
                await message.reply_photo(photo=graph, reply_markup=keyboard)
        else:
            await message.answer(f"По запросу: '{message.text}' не найдено ни одной зарплаты")
    except Exception as e:
        logging.error(e, exc_info=True)
        await message.answer(f"Возникла ошибка, обратитесь в поддержку или попробуйте снова через минуту")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('best_salary'))
async def show_best_salaries(callback_query: types.CallbackQuery):
    user = callback_query.message.chat.id
    try:
        text = await STORAGE.get_data(user=user)
        hh_obj = Hh()
        salaries = await hh_obj.get_best_salaries(text)
        answer = ''
        for salary in salaries:
            min_salary, max_salary = hh_obj.convert_salary(salary['salary'])
            answer += f"{salary['name']}, От {min_salary:,} До {max_salary:,} - {salary['alternate_url']}\n\n"

        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, answer)
    except Exception as e:
        logging.error(e, exc_info=True)
        await bot.send_message(callback_query.from_user.id,
                               f"Возникла ошибка, обратитесь в поддержку или попробуйте снова через минуту")
    finally:
        await STORAGE.reset_data(user=user)


@dp.message_handler()
async def main_tmpl(message):
    answer = """
/show_salary_graph - Построить график зарплат
/show_search_help - Подсказка для более точного поиска
       """
    await message.reply(answer)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    # start_webhook(
    #     dispatcher=dp,
    #     webhook_path=WEBHOOK_PATH,
    #     on_startup=on_startup,
    #     on_shutdown=on_shutdown,
    #     skip_updates=True,
    #     host=WEBAPP_HOST,
    #     port=WEBAPP_PORT,
    # )

