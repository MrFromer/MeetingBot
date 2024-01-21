import sqlite3 as sq

async def db_start():
    global db, cur #db - экземпляр (модель) базы данных \\\ cur - чтобы выполнять операции с базой данных
    db = sq.connect('new.db')
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS profile(user_id TEXT PRIMARY KEY, photo TEXT, name TEXT, age TEXT, location TEXT, description TEXT)") #тут мы создали саму таблицу и указали для неё поля с типами данных
    #user_id будет уникальным, в photo мы храним индефикатор фото
    db.commit()

async def create_profile(user_id):
    user = cur.execute("SELECT 1 FROM profile WHERE user_id == '{key}'".format(key=user_id)).fetchone() #если пользователь существует, то мы берём копируем его через fetchone. Через key мы проверяем, что это наш пользователь предварительно записав через format из user_id
    print(user)
    if not user: #если пользователь не существует
        cur.execute("INSERT INTO profile VALUES(?, ?, ?, ?, ?, ?)", (user_id, '', '', '', '', ''))
        db.commit()

async def save_profile(state, user_id):
    async with state.proxy() as data:
        cur.execute("UPDATE profile SET photo = '{}', name = '{}', age = '{}', location = '{}', description = '{}' WHERE user_id == '{}'".format(
            data['photo'], data['name'], data['age'], data['location'], data['description'], user_id))
        db.commit()

async def look_profile(user_id):
    profile = cur.execute("SELECT * FROM profile").fetchall() #выводим все данные из таблицы profile т.е каждый пользователь это будет кортеж
    return profile  #это список, где внутри кортежи

async def delete_profile(user_id):
    data = cur.execute("SELECT * FROM profile WHERE user_id == '{key}'".format(key=user_id)).fetchall()
    if len(data)==0:
        return len(data)
    else:
        cur.execute("DELETE FROM profile WHERE user_id == '{key}'".format(key=user_id))
        db.commit()
    

async def edit_profile_photo_db(state, user_id):
    async with state.proxy() as data_edit:
        cur.execute("UPDATE profile SET photo = '{}' WHERE user_id=='{}'".format(data_edit['photo'],user_id))
        db.commit()


async def edit_profile_name_db(state, user_id):
    async with state.proxy() as data_edit:
        cur.execute("UPDATE profile SET name = '{}' WHERE user_id=='{}'".format(data_edit['name'],user_id))
        db.commit()

async def edit_profile_age_db(state, user_id):
    async with state.proxy() as data_edit:
        cur.execute("UPDATE profile SET age = '{}' WHERE user_id=='{}'".format(data_edit['age'],user_id))
        db.commit()

async def edit_profile_location_db(state, user_id):
    async with state.proxy() as data_edit:
        cur.execute("UPDATE profile SET location = '{}' WHERE user_id=='{}'".format(data_edit['location'],user_id))
        db.commit()

async def edit_profile_description_db(state, user_id):
    async with state.proxy() as data_edit:
        cur.execute("UPDATE profile SET description = '{}' WHERE user_id=='{}'".format(data_edit['description'],user_id))
        db.commit()