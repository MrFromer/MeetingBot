from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN_API
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
import re
from sql import db_start, create_profile, edit_profile

storage = MemoryStorage() #хранилище для манины состояния FSM
bot = Bot(TOKEN_API)
dp  = Dispatcher(bot, storage=storage)

async def startup(_):
    await db_start() #подключение в бд
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
    await create_profile(user_id=message.from_user.id) #вызываем ф-цию для создания профиля в базе данных
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
    
#прописываем поэтапные дейстия по созданию профиля (этапы представлены в классе ниже), так-же есть ф-ци отмены создания через комманду /cancel
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
async def command_cancel(message: types.Message, state:FSMContext): #state:FSMContext означает, что переменную state мы обозначаем как FSMContext
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

@dp.message_handler(content_types=['photo'], state=Profile.photo) #state=Profile.photo - это проверка что мы сейчас находимся в состоянии ожидания photo
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data: #data - временное хранилище для состояний, потом в конце создания анкеты данные перенесутся в базу SQl
        data['photo'] = message.photo[0].file_id #во временное хранилище под индификатором photo сохраняем id фотографии, которую отправил пользователь

    await message.reply('Теперь отправь своё имя')
    await Profile.next()

@dp.message_handler(lambda message: not message.text.isalpha(), state=Profile.name)  #isalpha() - проверка на то, что в "text" пользователь ввёл данные в формате текста (т.е не символы и цифры) и в это время бот находится в состоянии ожидания имени
async def check_name(message: types.Message):
    await message.reply('Введите имя без цифр и символов!')

@dp.message_handler(state=Profile.name)
async def load_name(message: types.Message, state:FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply('Напиши свой возраст😝')
    await Profile.next()

@dp.message_handler(lambda message: not message.text.isdigit(), state=Profile.age)
async def ckeck_age(message: types.Message):
    await message.reply('Напишите возраст только цифрами!')

@dp.message_handler(state=Profile.age)
async def load_age(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
    await message.reply('Напишите свою страну и город в формате: "Страна,Город" ')
    await Profile.next()
    
#re.match('[А-я]+\,+[А-я]', str(message.text)) - регулярные выражения
@dp.message_handler(lambda message: not bool(re.match('[А-я]+\,+[А-я]', str(message.text))), state=Profile.location) #через регулярные выражения тут записано условие: что пользователь вводит сначала текст из заглавных и маленьких, потом сразу запятая и потом опять текст т.е формат "Страна,Город"
#@dp.message_handler(lambda message: (',' in message.text) and (not message.text.isdigit()), state=Profile.location)
async def ckeck_location(message: types.Message):
    await message.reply('Напишите свою локацию в формате: "Страна,Город" (строго, как в примере)')


@dp.message_handler(state=Profile.location)
async def load_location(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['location'] = message.text
    await message.reply('А теперь остался последний шаг! Опишите свои увлечения и хобби, а так-же напишите немного о себе в целом ')
    await Profile.next()

@dp.message_handler(state=Profile.desc)
async def load_location(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text

    await edit_profile(state, user_id=message.from_user.id)
    await bot.send_photo(chat_id=message.from_user.id, photo = data['photo'], caption=f"Ваша анкета: {data['name']}, {data['age']}, {data['location']}\n{data['description']}")    
    await message.reply('На этом всё, вы успешно создали анкету! Если вы что-то хотите в ней поменять, то у вас всегда есть такая возможность написав комманду /editprofile')
    await state.finish()



if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=startup)