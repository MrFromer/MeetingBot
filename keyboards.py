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