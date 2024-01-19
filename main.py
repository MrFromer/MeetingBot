from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN_API
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
import re
from database import db_start, create_profile, edit_profile, look_profile
from keyboards import kb, kb_cancel


storage = MemoryStorage() #хранилище для манины состояния FSM
bot = Bot(TOKEN_API)
dp  = Dispatcher(bot, storage=storage)

async def startup(_):
    await db_start() #подключение в бд
    print('Бот был успешно запущен')


###################################################################################################  блок базовых комманд
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

    
################################################################################################### блок взаимодействия пользователя со своим профилем 
#вывод текущего профиля пользователя (НУЖНО ДОРАБОТАТЬ ПРОВЕРКУ ID т.е что у определённого пользователя есть профиль)
@dp.message_handler(text='Посмотреть профиль')
async def watch_profile(message: types.Message):
    profiles = await look_profile(message.from_user.id)
    k = 0
    # if not profile:
    #     await message.reply('Вы ещё не создали профиль, для этого напишите комманду /create')
    # else:
    #     await bot.send_photo(chat_id=message.from_user.id,)
    for profile in profiles:
        if int(profile[0]) == int(message.from_user.id):
            k = 1
            break
    if k == 0:
        await message.reply('Вы ещё не создали профиль, для этого напишите комманду /create')
    elif k == 1:
        await bot.send_photo(chat_id=message.from_user.id, photo=profile[1], caption=f'Имя:{profile[2]} Возраст:{profile[3]} Локация:{profile[4]}, Описание профиля:{profile[5]}')
 





################################################################################################### блок поэтапного заполнения профиля
#прописываем поэтапные дейстия по созданию профиля (этапы представлены в классе ниже), так-же есть ф-ция отмены создания через комманду /cancel
class Profile(StatesGroup): #объекты с состояниями для FSM (машины состояний)
    photo = State()
    name = State()
    age = State()
    location = State()
    desc = State()
    
#функция для прерывания создания и завершается машина состояния
@dp.message_handler(text='Отменить', state='*') # * означает, что эта ф-ция будет работать в любом состоянии
async def command_cancel(message: types.Message, state:FSMContext): #state:FSMContext означает, что переменную state мы обозначаем как FSMContext
    if state is None: #если состояние пустое, то ничего не делает
        return
    
    await state.finish()
    await message.reply(text='Вы прервали создание анкеты, придётся создавать её заного!', reply_markup=kb)
#такая-же что и выше тольк принимает комманду на вход
@dp.message_handler(commands=['cancel'], state='*') # * означает, что эта ф-ция будет работать в любом состоянии
async def command_cancel(message: types.Message, state:FSMContext): #state:FSMContext означает, что переменную state мы обозначаем как FSMContext
    if state is None: #если состояние пустое, то ничего не делает
        return
    
    await state.finish()
    await message.reply(text='Вы прервали создание анкеты, придётся создавать её заного!', reply_markup=kb)

#начинаем процесс создания и устанавливаем FSM на состояние photo
@dp.message_handler(text='Создать профиль')
async def command_create(message: types.Message) -> None:
    await create_profile(user_id=message.from_user.id) #вызываем ф-цию для создания профиля в базе данных
    await message.reply(text='Вы начали создавать анкету! Для начала пришлите своё фото', reply_markup=kb_cancel)
    await Profile.photo.set() #обращаемся к классу Profile и ставим состояние на 'photo'
#такая-же что и выше тольк принимает комманду на вход
@dp.message_handler(commands=['create'])
async def command_create(message: types.Message) -> None:
    await create_profile(user_id=message.from_user.id) #вызываем ф-цию для создания профиля в базе данных
    await message.reply(text='Вы начали создавать анкету! Для начала пришлите своё фото', reply_markup=kb_cancel)
    await Profile.photo.set() #обращаемся к классу Profile и ставим состояние на 'photo'

#проверка на то, что пользователь отправил фото
@dp.message_handler(lambda message: not message.photo, state=Profile.photo) #проверка на то, что пользователь прислал фото (когда состояние равно 'photo')
async def ckeck_photo(message: types.Message):
    await message.reply('Это не фотография!')

#загрузка фото в временное хранилище (словарь) data
@dp.message_handler(content_types=['photo'], state=Profile.photo) #state=Profile.photo - это проверка что мы сейчас находимся в состоянии ожидания photo
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data: #data - временное хранилище для состояний, потом в конце создания анкеты данные перенесутся в базу SQl
        data['photo'] = message.photo[0].file_id #во временное хранилище под индификатором photo сохраняем id фотографии, которую отправил пользователь

    await message.reply('Теперь отправь своё имя')
    await Profile.next()

#проверка на текст
@dp.message_handler(lambda message: not message.text.isalpha(), state=Profile.name)  #isalpha() - проверка на то, что в "text" пользователь ввёл данные в формате текста (т.е не символы и цифры) и в это время бот находится в состоянии ожидания имени
async def check_name(message: types.Message):
    await message.reply('Введите имя без цифр и символов!')

#загрузка имени в словарь data в поле name
@dp.message_handler(state=Profile.name)
async def load_name(message: types.Message, state:FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.reply('Напиши свой возраст😝')
    await Profile.next()

#проверка на число и диапазон 7-100
@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100 or float(message.text) < 7, state=Profile.age)
async def ckeck_age(message: types.Message):
    await message.reply('Напишите свой реальный возраст!')

#загрузка возраста в словарь data под индификатором age
@dp.message_handler(state=Profile.age)
async def load_age(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
    await message.reply('Напишите свою страну и город в формате: "Страна,Город" ')
    await Profile.next()

#проверка на то, что пользователь ввёл текст по маске: "Страна,Город"    
#re.match('[А-я]+\,+[А-я]', str(message.text)) - регулярные выражения
@dp.message_handler(lambda message: not bool(re.match('[А-я]+\,+[А-я]', str(message.text))), state=Profile.location) #через регулярные выражения тут записано условие: что пользователь вводит сначала текст из заглавных и маленьких, потом сразу запятая и потом опять текст т.е формат "Страна,Город"
#@dp.message_handler(lambda message: (',' in message.text) and (not message.text.isdigit()), state=Profile.location)
async def ckeck_location(message: types.Message):
    await message.reply('Напишите свою локацию в формате: "Страна,Город" (строго, как в примере)')

#загрузка местоположения в словарь data под индификатором location
@dp.message_handler(state=Profile.location)
async def load_location(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['location'] = message.text
    await message.reply('А теперь остался последний шаг! Опишите свои увлечения и хобби, а так-же напишите немного о себе в целом ')
    await Profile.next()

#загрузка описани в словарь data и вывод итоговой анкеты, а так-же сохранение в базу данных sql из словаря data
@dp.message_handler(state=Profile.desc)
async def load_location(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
        await bot.send_photo(chat_id=message.from_user.id, photo = data['photo'], caption=f"Ваша анкета: {data['name']}, {data['age']}, {data['location']}\n{data['description']}")   

    await edit_profile(state, user_id=message.from_user.id) #сохраняем данные в бд
    await message.reply(text='На этом всё, вы успешно создали анкету! Если вы что-то хотите в ней поменять, то у вас всегда есть такая возможность написав комманду /editprofile',reply_markup=kb)
    await state.finish()

###############################################################



if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=startup)