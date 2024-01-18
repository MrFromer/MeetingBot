from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN_API
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext


storage = MemoryStorage() #хранилище для манины состояния FSM
bot = Bot(TOKEN_API)
dp  = Dispatcher(bot, storage=storage)

async def startup(_):
    print('Бот был успешно запущен')

#блок базовых комманд
###################################################################################################
TEXT_START = '''
Добро пожаловать в наш бот! 
👉🏼Вот что он умеет:
<b>/start</b> - вводная информация
<b>/create</b> - создать профиль пользователя
<b>/cancel</b> - отменить создание профиля
<b>/editprofile</b> - редактировать существующий профиль
<b>/deleteprofile</b> - удалить профиль
<b>/description</b> - описание бота и его возможностей
'''

@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    await bot.send_sticker(chat_id= message.chat.id, sticker="CAACAgIAAxkBAAEKoONlPeHJlBXIIlquMX1oVutb58B-tAACiwEAAiteUwujYbxpJDSDUDAE")
    await bot.send_message(chat_id=message.chat.id, text=TEXT_START, parse_mode='HTML', reply_markup=kb)
    await message.delete()

TEXT_DESCRIPTION = '''
Наш бот активно развивается и постоянно добавляются новые функции!
Следи за обновлениями и предлагай свои.
'''
@dp.message_handler(commands=['description'])
async def command_start(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=TEXT_DESCRIPTION, parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
    await message.delete()
###################################################################################################
    
#прописываем поэтапные дейстия по созданию профиля (этапы представлены в классе ниже)
class Profile(StatesGroup): #объекты с состояниями для FSM (машины состояний)
    photo = State()
    name = State()
    age = State()
    location = State()
    desc = State()
    
#основная клавиатура (главная)
kb = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True, keyboard=[
    [KeyboardButton(text='/create'), KeyboardButton(text='/edit_profile')],
    [KeyboardButton(text='/profile'), KeyboardButton(text='/delete_profile')]
])

#побочная клавиатуры (для возврата в меню или отмены создания профиля)
kb_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[
    [KeyboardButton(text='/cancel')]
])

@dp.message_handler(commands=['cancel'], state='*') # * означает, что эта ф-ция будет работать в любом состоянии
async def command_cancel(message: types.Message, state:FSMContext):
    if state is None: #если состояние пустое, то ничего не делает
        return
    
    await state.finish()
    await message.reply(text='Вы прервали создание анкеты, придётся создавать её заного!', reply_markup=kb)

@dp.message_handler(commands=['create'])
async def command_create(message: types.Message) -> None:
    await message.reply(text='Вы начали создавать анкету! Для начала пришлите своё фото', reply_markup=kb_cancel)
    await Profile.photo.set() #обращаемся к классу Profile и ставим состояние на 'photo'

@dp.message_handler(lambda message: not message.photo, state=Profile.photo) #проверка на то, что пользователь прислал фото (когда состояние равно 'photo')
async def ckeck_photo(message: types.Message):
    await message.reply('Это не фотография!')

@dp.message_handler(content_types=['photo'], state=Profile.photo)
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data: #data - временное хранилище для состояний
        data['photo'] = message.photo[0].file_id #во временное хранилище под индификатором photo сохраняем id фотографии, которую отправил пользователь

    
    await message.reply('Теперь отправь своё имя')
    await Profile.next()

#@dp.message_handler(commands=[''])


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=startup)