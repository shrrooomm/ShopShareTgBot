import aiosqlite as sq

DB_NAME = 'ShopShare.db'

#Инициализация базы данных
async def db_start():
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")

        await db.execute("CREATE TABLE IF NOT EXISTS users("
                "tg_id INTEGER PRIMARY KEY,"
                "name TEXT)")
         
        await db.execute("CREATE TABLE IF NOT EXISTS lists("
                "list_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "title TEXT NOT NULL,"
                "creator_id INTEGER,"
                "FOREIGN KEY (creator_id) REFERENCES users (tg_id) ON DELETE CASCADE)")
         
        await db.execute("CREATE TABLE IF NOT EXISTS user_lists("
                "user_id INTEGER,"
                "list_id INTEGER,"
                "PRIMARY KEY (user_id, list_id),"
                "FOREIGN KEY (user_id) REFERENCES users (tg_id) ON DELETE CASCADE,"
                "FOREIGN KEY (list_id) REFERENCES lists (list_id) ON DELETE CASCADE)")
         
        await db.execute("CREATE TABLE IF NOT EXISTS products("
                "product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "list_id INTEGER,"
                "title TEXT NOT NULL,"
                "quantity TEXT,"
                "is_urgent INTEGER DEFAULT 0,"
                "is_bought INTEGER DEFAULT 0,"
                "photo_id TEXT DEFAULT NULL,"
                "FOREIGN KEY (list_id) REFERENCES lists (list_id) ON DELETE CASCADE)")
        await db.commit()

#Возврат названия списка по его ID
async def get_list_title(list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        async with db.execute("SELECT title FROM lists WHERE list_id = ?", (list_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

#Возврат TG ID создателя списка по ID списка
async def get_list_creator(list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        async with db.execute("SELECT creator_id FROM lists WHERE list_id = ?", (list_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

#Добавление нового пользователя или обновление имени существующего
async def add_user(tg_id, name):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("INSERT OR REPLACE INTO users (tg_id, name) VALUES (?, ?)",
                         (tg_id, name))
        await db.commit()

#Создание нового списка, связь с создателем и возврат ID списка
async def create_list(title, creator_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        cur = await db.execute("INSERT INTO lists (title, creator_id) VALUES (?, ?)", 
                         (title, creator_id))
        list_id = cur.lastrowid
        await db.execute("INSERT INTO user_lists (user_id, list_id) VALUES (?, ?)", 
                         (creator_id, list_id))
        await db.commit()
        return list_id

#Возврат списка всех товаров в списке
async def get_products(list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        db.row_factory = sq.Row
        async with db.execute("SELECT * FROM products WHERE list_id = ?", (list_id,)) as cursor:
            return await cursor.fetchall()

#Возврат всех списков пользователя (свои и чужие)
async def get_user_lists(user_id, is_creator = True):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        db.row_factory = sq.Row
        if is_creator:
            async with db.execute("SELECT * FROM lists WHERE creator_id = ?", (user_id,)) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute("SELECT l.list_id, l.title FROM lists l "
                "JOIN user_lists ul ON l.list_id = ul.list_id "
                "WHERE ul.user_id = ? AND l.creator_id != ?", 
                (user_id, user_id)) as cursor:
                return await cursor.fetchall()

#Добавление нового товара в указанный список
async def add_product(list_id, title, quantity, is_urgent):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("INSERT INTO products (list_id, title, quantity, is_urgent) VALUES (?, ?, ?, ?)",
                          (list_id, title, quantity, is_urgent))
        await db.commit()

#Удаление товара из базы данных по ID
async def delete_product(product_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        await db.commit()

#Переключение статуса срочности на противоположный
async def switch_urgent(product_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("UPDATE products SET is_urgent = NOT is_urgent WHERE product_id = ?", (product_id,))
        await db.commit()

#Переключение статуса 'куплено' на противоположный
async def switch_bought(product_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("UPDATE products SET is_bought = NOT is_bought WHERE product_id = ?", (product_id,))
        await db.commit()

#Удаление списка покупок по его ID
async def delete_list(list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("DELETE FROM lists WHERE list_id = ?", (list_id,))
        await db.commit()

#Проверка привязанности пользователя к указанному списку
async def is_user_in_list(user_id, list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        async with db.execute('SELECT 1 FROM user_lists WHERE user_id = ? AND list_id = ?', (user_id, list_id)) as cursor:
            return await cursor.fetchone() is not None

#Добавление пользователя в список участников
async def add_user_to_list(user_id, list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute('INSERT OR IGNORE INTO user_lists (user_id, list_id) VALUES (?, ?)', (user_id, list_id))
        await db.commit()

#Удаление пользователя из участников списка
async def remove_user_from_list(user_id, list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("DELETE FROM user_lists WHERE user_id = ? AND list_id = ?", (user_id, list_id))
        await db.commit()

#Возврат списка всех участников указанного списка
async def list_members(list_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        db.row_factory = sq.Row
        async with db.execute("SELECT u.tg_id, u.name, "
            "CASE WHEN u.tg_id = l.creator_id THEN 1 ELSE 0 END as is_creator "
            "FROM users u "
            "JOIN user_lists ul ON u.tg_id = ul.user_id "
            "JOIN lists l ON ul.list_id = l.list_id "
            "WHERE ul.list_id = ?", (list_id,)
        ) as cursor:
            return await cursor.fetchall()

#Проверка регистрации пользователя в боте
async def is_user_registered(user_id):
    async with sq.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        async with db.execute("SELECT name FROM users WHERE tg_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            return res[0] if res else None