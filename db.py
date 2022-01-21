import sqlite3

# Потокобезопасное подключение. Не открываем соединение в каждой функции, только в декораторе

def ensure_connection(funct):

    def inlay(*args, **kwargs):
        with sqlite3.connect('vault.db') as conn:
            res = funct(*args, conn=conn, **kwargs)
        return res
    return inlay


@ensure_connection
def init_db(conn, force: bool = False):
    ''':param force: явно пересоздать все таблицы'''

    c = conn.cursor()

    if force:
        c.execute('DROP TABLE IF EXISTS user_data') # Если стоит флаг force, удалим таблицу, если она уже существует. Если сразу запустить код с этим флагом, то он не упадет.
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id          INTEGER PRIMARY KEY,
            actual_name TEXT NOT NULL,
            user_id     INTEGER NOT NULL,
            chat_id     INTEGER NOT NULL,
            nickname    TEXT NOT NULL,
            answer      INTEGER,
            rating      INTEGER,
            score       INTEGER
        )
    ''')

    conn.commit()


@ensure_connection
def signup(conn, actual_name: str, user_id: int, chat_id: int, nickname: str, answer: int, rating: int, score: int):

    c = conn.cursor()
    c.execute('SELECT actual_name, user_id, nickname FROM user_data WHERE actual_name=? OR user_id=? OR nickname=?', (actual_name, user_id, nickname))
    if not (result := c.fetchone()):
        c.execute('INSERT INTO user_data (actual_name, user_id, chat_id, nickname, answer, rating, score) VALUES (?, ?, ?, ?, ?, ?, ?)', (actual_name, user_id, chat_id, nickname, answer, rating, score))
        conn.commit()

        return 'OK'


@ensure_connection
def get_chat_ids(conn):
    '''produces only unique chat_ids'''

    c = conn.cursor()
    result = [chat_id[0] for chat_id in c.execute('SELECT chat_id FROM user_data')]

    return set(result)


@ensure_connection
def write_answers(conn, user_id: int):

    c = conn.cursor()
    c.execute('UPDATE user_data SET answer=1 WHERE user_id=?', (user_id, ))
    c.execute('SELECT nickname FROM user_data WHERE user_id=?', (user_id, ))

    result = c.fetchone()
    conn.commit()

    return result[0]


@ensure_connection
def write_score(conn, rating: int, nickname: str):

    c = conn.cursor()
    c.execute('UPDATE user_data SET rating=? WHERE nickname=?', (rating, nickname))
    c.execute('UPDATE user_data SET score=score+? WHERE nickname=?', (rating, nickname))
    conn.commit()


@ensure_connection
def did_they_answer(conn, user_id: int):

    c = conn.cursor()
    c.execute('SELECT answer FROM user_data WHERE user_id = ?', (user_id, ))
    result = c.fetchone()
    print(result)

    return result[0]


@ensure_connection
def round_rating(conn):

    c = conn.cursor()
    result1 = [nickname[0] for nickname in c.execute('SELECT nickname FROM user_data WHERE rating=?', (2, ))]
    result2 = [nickname[0] for nickname in c.execute('SELECT nickname FROM user_data WHERE rating=?', (1, ))]

    c.execute('UPDATE user_data SET answer=0, rating=0')
    conn.commit()

    return (result1, result2)


@ensure_connection
def total_score(conn):
    
    c = conn.cursor()
    c.execute('SELECT GROUP_CONCAT(nickname), score FROM (SELECT score, nickname FROM user_data ORDER BY score, nickname) GROUP BY score;')
    return c.fetchall()


@ensure_connection
def delete_score(conn):

    c = conn.cursor()
    c.execute('DROP TABLE user_data')