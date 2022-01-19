import logging

from hh_connector import Hh
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
    await message.reply("Чтобы получить график интересующих вас зарплат, введите должность, которую вы ищете")
    await ShowSalaryGraph.waiting_for_specialisation.set()
    return


@dp.message_handler(state=ShowSalaryGraph.waiting_for_specialisation)
async def enter_specialisation(message: types.Message, state: FSMContext):
    await message.answer(f"Необходимо немного подождать. Обычно не больше 10 секунд . . .")
    hh_obj = Hh()
    try:
        salaries = await hh_obj.get_salary_normal(message.text)
        graph = hh_obj.get_graph(salaries)

        await message.answer(f"График зарплат по профессии: {message.text}")
        await message.reply_photo(photo=graph)
        graph.close()
    except Exception as e:
        logging.error(e, exc_info=True)
        await message.answer(f"Возникла ошибка, обратитесь в поддержку или попробуйте снова через минуту")
    await state.finish()


@dp.message_handler()
async def answer_tmpl(message):
    answer = """
       /show_salary_graph - Построить график зарплат
       """
    await message.reply(answer)


if __name__ == "__main__":
    executor.start_polling(dp)