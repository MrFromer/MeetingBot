from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

#основная клавиатура (главная)
kb = ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=True, keyboard=[
    [KeyboardButton(text='Создать профиль'), KeyboardButton(text='Редактировать профиль')],
    [KeyboardButton(text='Посмотреть профиль'), KeyboardButton(text='Удалить профиль')]
])

#побочная клавиатуры (для возврата в меню или отмены создания профиля)
kb_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[
    [KeyboardButton(text='Отменить')]
])

ikb_edit = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Имя',callback_data='btn_name'), InlineKeyboardButton(text='Описание',callback_data='btn_description'),InlineKeyboardButton(text='Фото',callback_data='btn_photo')],
    [InlineKeyboardButton(text='Локацию',callback_data='btn_location'),InlineKeyboardButton(text='Возраст',callback_data='btn_age')],
    
])

kb_return = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text='Вернуться в главное меню')]
])