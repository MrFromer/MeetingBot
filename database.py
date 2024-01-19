import sqlite3 as sq

async def db_start():
    global db, cur #db - экземпляр (модель) базы данных \\\ cur - чтобы выполнять операции с базой данных
    db = sq.connect('new.db')
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS profile(user_id TEXT PRIMARY KEY, photo TEXT, name TEXT, age TEXT, location TEXT, description TEXT)") #тут мы создали саму таблицу и указали для неё поля с типами данных
    #user_id будет уникальным, в photo мы храним индефикатор фото
    db.commit()

async def create_profile(user_id):
    user = cur.execute("SELECT 1 FROM profile WHERE user_id == '{key}'".format(key=user_id)).fetchone() #если пользователь существует, то мы берём копируем его через fetchone. И где поле user_id означает ключ, который в свою очередь через format мы обозначаем, как сам id пользователя, остальные поля пустые
    if not user: #если пользователь не существует
        cur.execute("INSERT INTO profile VALUES(?, ?, ?, ?, ?, ?)", (user_id, '', '', '', '', ''))
        db.commit()

async def edit_profile(state, user_id):
    async with state.proxy() as data:
        cur.execute("UPDATE profile SET photo = '{}', name = '{}', age = '{}', location = '{}', description = '{}' WHERE user_id == '{}'".format(
            data['photo'], data['name'], data['age'], data['location'], data['description'], user_id))
        db.commit()

async def look_profile(user_id):
    profile = cur.execute("SELECT * FROM profile").fetchall() #выводим все данные из таблицы profile т.е каждый пользователь это будет кортеж
    print(profile)
    return profile  # list