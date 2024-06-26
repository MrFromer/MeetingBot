from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN_API
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
import re
from database import db_start, create_profile, save_profile, look_profile, delete_profile, edit_profile_photo_db, edit_profile_name_db, edit_profile_age_db, edit_profile_location_db, edit_profile_description_db, update_log_look
from keyboards import kb, kb_cancel, ikb_edit, ikb_look
import tracemalloc

tracemalloc.start()
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
<b>/edit</b> - редактировать существующий профиль
<b>/delete</b> - удалить профиль
<b>/profile</b> - посмотреть профиль
<b>/description</b> - описание бота и его возможностей
<b>/return</b> - вернуться в главное меню
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
@dp.message_handler(text='Просмотреть свой профиль')
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
        await bot.send_photo(chat_id=message.from_user.id, photo=profile[1], caption=f'Имя: {profile[2]}; Возраст: {profile[3]}; Локация: {profile[4]};\nОписание профиля: {profile[5]};')

#тоже самое только через комманду
@dp.message_handler(commands=['profile'])
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
        await bot.send_photo(chat_id=message.from_user.id, photo=profile[1], caption=f'Имя: {profile[2]}; Возраст: {profile[3]}; Локация: {profile[4]};\nОписание профиля: {profile[5]};')    


#удаление текущего профиля
@dp.message_handler(text='Удалить профиль')
async def delet_profile(message: types.Message):
    data = await delete_profile(message.from_user.id)
    if data == 0:
        await message.reply('Вы ещё не создали профиль, для этого напишите /create')
    else:
        await delete_profile(message.from_user.id) #ф-ция из файла database для удаления профиля 
        await message.reply('Ваш профиль был удалён, если вы хотите создать его заного нажмита на /create')

#тоже самое, только через комманду
@dp.message_handler(commands=['delete'])
async def delet_profile(message: types.Message):
    data = await delete_profile(message.from_user.id)
    if data == 0:
        await message.reply('Вы ещё не создали профиль, для этого напишите /create')
    else:
        await delete_profile(message.from_user.id) #ф-ция из файла database для удаления профиля 
        await message.reply('Ваш профиль был удалён, если вы хотите создать его заного нажмита на /create')
    

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

#такая-же что и выше только принимает комманду на вход
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
        data['viewed_profiles'] = str(message.from_user.id)
        await bot.send_photo(chat_id=message.from_user.id, photo = data['photo'], caption=f"Ваша анкета --> Имя: {data['name']}; Возраст: {data['age']}; Локация: {data['location']};\nОписание: {data['description']};")   

    await save_profile(state, user_id=message.from_user.id) #сохраняем данные в бд
    await message.reply(text='На этом всё, вы успешно создали анкету! Если вы что-то хотите в ней поменять, то у вас всегда есть такая возможность написав комманду /editprofile',reply_markup=kb)
    await state.finish()




###############################################################   блок изменения профиля
@dp.message_handler(commands=['edit'])
async def call_edit_profile(message: types.Message):
    profiles = await look_profile(message.from_user.id)
    k = 0
    for profile in profiles:
        if int(profile[0]) == int(message.from_user.id):
            k = 1
            break
    if k == 0:
        await message.reply('Вы ещё не создали профиль, для этого напишите комманду /create')
    elif k == 1:
        await bot.send_photo(chat_id=message.from_user.id, photo=profile[1], caption=f'Имя: {profile[2]}; Возраст: {profile[3]}; Локация: {profile[4]};\nОписание профиля: {profile[5]};')
        await message.reply(text='Вот ваша анкета, что конкретно вы хотите изменить? Выберите из меню ниже:',reply_markup=ikb_edit)
#тоже самое, только через текст
@dp.message_handler(text='Редактировать профиль')
async def call_edit_profile(message: types.Message):
    profiles = await look_profile(message.from_user.id) #принимаем кортеж с профилями
    k = 0
    for profile in profiles: #через цикл пробегаемся по профилям и ищем нужный индификатор пользователя
        if int(profile[0]) == int(message.from_user.id):
            k = 1
            break
    if k == 0: #если пользователя в БД нет
        await message.reply('Вы ещё не создали профиль, для этого напишите комманду /create')
    elif k == 1: #если пользователя в БД есть
        await bot.send_photo(chat_id=message.from_user.id, photo=profile[1],  caption=f'Имя: {profile[2]}; Возраст: {profile[3]}; Локация: {profile[4]};\nОписание профиля: {profile[5]};')
        await message.reply(text='Вот ваша анкета, что конкретно вы хотите изменить? Выберите из меню ниже:',reply_markup=ikb_edit)

#ф-ция для возврата в главное меню
# @dp.message_handler(text='Вернуться в главное меню') #функция будет работать в любом состоянии
# async def go_to_main_menu(message: types.Message):
#     await message.answer(text='Вы вернулись в главное меню!',reply_markup=kb)

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'btn_return')
async def edit_return(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id, text='Вы вернулись в главное меню!', reply_markup=kb)
    

#ф-ция для возврата в главное меню через комманду
@dp.message_handler(commands=['return'])
async def go_to_main_menu_cmd(message: types.Message):
    await message.answer(text='Вы вернулись в главное меню!',reply_markup=kb)

#прописываю практически тоже самое что и в создании (т.е поэтапное создание), но сделано под функционал изменения профиля т.е на каждом этапе отправляем данные в БД и для каждой кнопки в "database" написана функция (в этом основное отличие) 
class Profile_edit(StatesGroup): #объекты с состояниями для FSM (машины состояний)
    photo = State()
    name = State()
    age = State()
    location = State()
    desc = State()
    

#если пользователь хочет изменить фото
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'btn_photo')
async def edit_profile_photo(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id, text='Хорошо, пришлите своё фото')
    await Profile_edit.photo.set()

#проверка на то, что пользователь отправил фото
@dp.message_handler(lambda message: not message.photo, state=Profile_edit.photo) #проверка на то, что пользователь прислал фото (когда состояние равно 'photo')
async def ckeck_photo_edit(message: types.Message):
    await message.reply('Это не фотография!')

#загрузка фото во временное хранилище (словарь) data
@dp.message_handler(content_types=['photo'], state=Profile_edit.photo) #state=Profile.photo - это проверка что мы сейчас находимся в состоянии ожидания photo
async def load_photo_edit(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data_edit: #data_edit - временное хранилище для данных, которые мы сразу перенаправим в БД
        data_edit['photo'] = message.photo[0].file_id #во временное хранилище под индификатором photo сохраняем id фотографии, которую отправил пользователь

    await edit_profile_photo_db(state, message.from_user.id)
    await message.reply(text='Мы сохранили вашу фотографию, если хотите изменить что-то ещё - выберите ниже:', reply_markup=ikb_edit)
    await state.finish()

#если пользователь хочет изменить имя
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'btn_name')
async def edit_profile_name(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id, text='Хорошо, пришлите новое имя')
    await Profile_edit.name.set()

#проверка на текст
@dp.message_handler(lambda message: not message.text.isalpha(), state=Profile_edit.name)  #isalpha() - проверка на то, что в "text" пользователь ввёл данные в формате текста (т.е не символы и цифры) и в это время бот находится в состоянии ожидания имени
async def check_name_edit(message: types.Message):
    await message.reply('Введите имя без цифр и символов!')

#загрузка имени во временное хранилище (словарь) data_edit и потом сразу в базу данных
@dp.message_handler(state=Profile_edit.name) 
async def load_name_edit(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data_edit: #data_edit - временное хранилище для данных, которые мы сразу перенаправим в БД
        data_edit['name'] = message.text 

    await edit_profile_name_db(state, message.from_user.id)
    await message.reply(text='Мы сохранили новое имя, если хотите изменить что-то ещё - выберите ниже:', reply_markup=ikb_edit)
    await state.finish()


#если пользователь хочет изменить возраст
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'btn_age')
async def edit_profile_age(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id, text='Хорошо, пришлите свой возраст')
    await Profile_edit.age.set()

#проверка на число и диапазон 7-100
@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100 or float(message.text) < 7, state=Profile_edit.age)
async def ckeck_age_edit(message: types.Message):
    await message.reply('Напишите свой реальный возраст!')

#загрузка возраст во временное хранилище (словарь) data_edit и потом сразу в базу данных
@dp.message_handler(state=Profile_edit.age) 
async def load_age_edit(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data_edit: #data_edit - временное хранилище для данных, которые мы сразу перенаправим в БД
        data_edit['age'] = message.text 

    await edit_profile_age_db(state, message.from_user.id)
    await message.reply(text='Мы сохранили ваш возраст, если хотите изменить что-то ещё - выберите ниже:', reply_markup=ikb_edit)
    await state.finish()


#если пользователь хочет изменить локацию
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'btn_location')
async def edit_profile_location(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id, text='Хорошо, пришлите свою локацию в формате: "Страна,Город"')
    await Profile_edit.location.set()

#проверка на маску "Страна,Город"
@dp.message_handler(lambda message: not bool(re.match('[А-я]+\,+[А-я]', str(message.text))), state=Profile.location) #через регулярные выражения тут записано условие: что пользователь вводит сначала текст из заглавных и маленьких, потом сразу запятая и потом опять текст т.е формат "Страна,Город"
#@dp.message_handler(lambda message: (',' in message.text) and (not message.text.isdigit()), state=Profile.location)
async def ckeck_location_edit(message: types.Message):
    await message.reply('Напишите свою локацию в формате: "Страна,Город" (строго, как в примере Пример: Россия,Москва)')

#загрузка локации во временное хранилище (словарь) data_edit и потом сразу в базу данных
@dp.message_handler(state=Profile_edit.location) 
async def load_location_edit(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data_edit: #data_edit - временное хранилище для данных, которые мы сразу перенаправим в БД
        data_edit['location'] = message.text 

    await edit_profile_location_db(state, message.from_user.id)
    await message.reply(text='Мы сохранили вашу новую локацию, если хотите изменить что-то ещё - выберите ниже:', reply_markup=ikb_edit)
    await state.finish()


#если пользователь хочет изменить описание
@dp.callback_query_handler(lambda callback_query: callback_query.data == 'btn_description')
async def edit_profile_description(callback: types.CallbackQuery):
    await bot.send_message(chat_id=callback.from_user.id, text='Хорошо, пришлите новое описание!')
    await Profile_edit.desc.set()

#загрузка описания во временное хранилище (словарь) data_edit и потом сразу в базу данных
@dp.message_handler(state=Profile_edit.desc) 
async def load_location_edit(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data_edit: #data_edit - временное хранилище для данных, которые мы сразу перенаправим в БД
        data_edit['description'] = message.text 

    await edit_profile_description_db(state, message.from_user.id)
    await message.reply(text='Мы сохранили новое описание, если хотите изменить что-то ещё - выберите ниже:', reply_markup=ikb_edit)
    await state.finish()



############################################################################### блок просмотра чужих анкет и взаимодействия с ними
class Profile_looks(StatesGroup): #объекты с состояниями для FSM (машины состояний)
    callbackme = State()
    giveankety = State()
    

@dp.message_handler(text='Смотреть анкеты')
async def look_anketi(message: types.Message) -> None:
    print('Зашёл в 1')
    await message.reply(text='Начинаем смотреть анкеты?')
    await give_ankety(types.Message,FSMContext)
    
async def findporfile(iduser):
    profiles = await look_profile(iduser)
    for profile in profiles: #находим текущего пользователя по ID и сохраняем в "viewed_profiles" ID просмотренных профилей до этого
        if str(profile[0]) == str(iduser):
            return str(profile[6]) 
            

@dp.message_handler()
async def give_ankety(message: types.Message, state: FSMContext):
    print('Зашёл во 2')
    profiles = await look_profile(message.from_user.id)
    viewed_profile = await findporfile(message.from_user.id)
    global ID  
    k = 0
    for profile in profiles:
            if str(profile[0]) not in viewed_profile:
                k = 1
                ID = int(profile[0])
                viewed_profile+= f',{ID}'
                await bot.send_photo(chat_id=message.from_user.id, photo=profile[1], 
                                    caption=f'Имя: {profile[2]}; Возраст: {profile[3]}; Локация: {profile[4]};\nОписание профиля: {profile[5]};', reply_markup=ikb_look)
                async with state.proxy() as data_look: #сохраняем просмотренный ID в бд
                    data_look['viewed_profiles'] = viewed_profile
                await update_log_look(state, message.from_user.id)
                await Profile_looks.callbackme.set()
                break

    if k == 0:
        await message.reply('Вы просмотрели уже все профили')
        await state.finish()


@dp.callback_query_handler(state= Profile_looks.callbackme)
async def callback_look_anketi(callback: types.CallbackQuery):
    print('Зашёл в 3')
    
    if callback.data == 'writeprofile':
        await bot.send_message(chat_id=callback.from_user.id,text=f'Мы рады что вас кто-то заинтересовал, вот ID этого пользователя: @{ID} Можете ему написать :D')
    elif callback.data == 'nextprofile':
        await give_ankety(types.Message,FSMContext)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True, on_startup=startup)