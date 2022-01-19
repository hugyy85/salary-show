import logging
from statistics import mean, mode, median

from hh_connector import Hh
from graph import Graph
from config import TG_BOT_TOKEN

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


class ShowSalaryGraph(StatesGroup):
    waiting_for_specialisation = State()


@dp.message_handler(commands=["show_salary_graph"], state='*')
async def show_salary_graph(message: types.Message):
    await message.reply("""Чтобы получить график интересующих вас зарплат, введите название *должности* или *навык*""", parse_mode="Markdown")
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
    hh_obj = Hh()
    try:
        salaries = await hh_obj.get_salary_normal(message.text)
        if salaries:
            with Graph(salaries) as graph:
                await message.answer(f"График зарплат по профессии: {message.text}")
                await message.answer(f"""Среднее значение: {round(mean(salaries)):,} р.\nМода(зарплата которая встречается чаще других): {round(mode(salaries)):,}р.\nМедиана:{round(median(salaries)):,}""")
                await message.reply_photo(photo=graph)
        else:
            await message.answer(f"По запросу: '{message.text}' не найдено ни одной зарплаты")
    except Exception as e:
        logging.error(e, exc_info=True)
        await message.answer(f"Возникла ошибка, обратитесь в поддержку или попробуйте снова через минуту")

    await state.finish()


@dp.message_handler()
async def main_tmpl(message):
    answer = """
/show_salary_graph - Построить график зарплат
/show_search_help - Подсказка для более точного поиска
       """
    await message.reply(answer)


if __name__ == "__main__":
    executor.start_polling(dp)