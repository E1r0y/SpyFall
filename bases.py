import sqlite3

conn = sqlite3.connect('spyfall.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lobbies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        admin_id INTEGER NOT NULL,
        players TEXT NOT NULL
    )
''')


def reset_table():
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lobbies")
    cursor.execute("DELETE FROM SQLITE_SEQUENCE WHERE name = 'lobbies'")
    conn.commit()


def increment_check(id=10):
    cursor.execute('SELECT EXISTS(SELECT 1 FROM lobbies WHERE id = ? LIMIT 1)', (id,))
    result = cursor.fetchone()
    return result[0] == True


def create_lobby(name, admin_id):
    cursor.execute('INSERT INTO lobbies (name, admin_id, players) VALUES (?, ?, ?)', (name, admin_id, str(admin_id)))
    conn.commit()
    return cursor.lastrowid


def join_lobby(lobby_id, player_id):
    cursor.execute('UPDATE lobbies SET players = players || ? WHERE id=?', (',' + str(player_id), lobby_id))
    if cursor.rowcount > 0:
        conn.commit()
        return True
    else:
        return False


def leave_lobby(player_id):
    cursor.execute('SELECT name, admin_id, players FROM lobbies WHERE players LIKE ?', (f'%{player_id}%',))
    result = cursor.fetchone()

    if not result:
        return False, False, None

    name, admin_id, players_str = result
    if player_id == admin_id:
        cursor.execute('DELETE FROM lobbies WHERE name = ?', (name,))
        conn.commit()
        return True, True, name
    else:
        players = players_str.split(',')
        players.remove(str(player_id))
        players = ','.join(players)
        cursor.execute('UPDATE lobbies SET players=? WHERE name = ?', (players, name))
        conn.commit()
        return True, False, name


def get_lobby_id(name):
    cursor.execute('SELECT id FROM lobbies WHERE name = ?', (name,))
    lobby_id = cursor.fetchone()
    return lobby_id[0] if lobby_id else False


def get_all_lobbies():
    cursor.execute('SELECT id, name, admin_id, players FROM lobbies')
    rows = cursor.fetchall()
    return rows


def get_lobby_by_player(player_id):
    cursor.execute('SELECT name FROM lobbies WHERE players LIKE ?', (f'%{player_id}%',))
    lobby_name = cursor.fetchone()
    return lobby_name[0] if lobby_name else False


def get_lobby_players_str_by_name(lobby_name):
    cursor.execute('SELECT players FROM lobbies WHERE name = ?', (lobby_name,))
    players_str = cursor.fetchone()
    return players_str[0]


def check_admin_id_by_name(name):
    cursor.execute('SELECT admin_id FROM lobbies WHERE name = ?', (name,))
    admin_id = cursor.fetchone()
    return admin_id[0]


def check_admin_id_by_id(id):
    cursor.execute('SELECT admin_id FROM lobbies WHERE id = ?', (id,))
    admin_id = cursor.fetchone()
    return admin_id[0]


def check_if_in_lobby(player_id):
    cursor.execute('SELECT name FROM lobbies WHERE players LIKE ?', (f'%{player_id}%',))
    lobby_name = cursor.fetchone()
    return lobby_name[0] if lobby_name else False
