import sqlite3


def get_connection():
    return sqlite3.connect('timepad.db')


class Connector:
    def __init__(self):
        self.connection = get_connection()

    def add_user(self, chat_id, tg_username):
        # TODO: catch exceptions
        tg_username = tg_username.lower()
        c = self.connection.cursor()
        c.execute('INSERT INTO users(chatId, telegramName) '
                  'VALUES (?, ?)',
                  (chat_id, tg_username))
        self.connection.commit()

    def get_user_for_crawl(self):
        c = self.connection.cursor()
        c.execute('SELECT id, token, telegramName FROM users '
                  'WHERE token IS NOT NULL '
                  'ORDER BY introspectTimestamp LIMIT 1')
        result = c.fetchone()
        if result is not None:
            return {
                'id': result[0],
                'token': result[1],
                'tg_name': result[2]
            }
        return None

    def get_subscribers(self, user_id):
        c = self.connection.cursor()
        c.execute('SELECT subscriberId FROM subscriptions WHERE userId = ?', (user_id,))
        result = map(lambda row: row[0], c.fetchall())
        return list(result)

    def get_user_events(self, user_id):
        c = self.connection.cursor()
        c.execute('SELECT eventId FROM users_events WHERE userId = ?', (user_id,))
        events = map(lambda row: row[0], c.fetchall())
        return events

    def add_user_events(self, user_id, events):
        c = self.connection.cursor()
        user_events = map(lambda event: (user_id, event), events)
        c.executemany('INSERT OR IGNORE INTO users_events(userId, eventId) VALUES (?, ?)', user_events)
        self.connection.commit()

    def get_user_by_chat_id(self, chat_id):
        c = self.connection.cursor()
        c.execute('SELECT id, timepadId, token FROM users WHERE chatId = ?', (chat_id,))
        result = c.fetchone()
        if result is not None:
            return {
                'id': result[0],
                'timepadId': result[1],
                'token': result[2]
            }
        return None

    def set_timepad_data_for_chat_id(self, chat_id, timepad_id, email, token, city, last_timestamp):
        c = self.connection.cursor()
        c.execute('UPDATE users SET timepadId = ?, email = ?, token = ?, cityName = ?, introspectTimestamp = ? '
                  'WHERE chatId = ?', (timepad_id, email, token, city, last_timestamp, chat_id))
        self.connection.commit()

    def get_user_by_telegram(self, login):
        login = login.lower()
        c = self.connection.cursor()
        c.execute('SELECT id FROM users WHERE telegramName = ?', (login,))
        result = c.fetchone()
        if result is not None:
            return result[0]
        return None

    def add_subscription(self, user_id, subscriber_id):
        c = self.connection.cursor()
        c.execute('INSERT OR IGNORE INTO subscriptions(userId, subscriberId) '
                  'VALUES(?, ?)', (user_id, subscriber_id))
        self.connection.commit()

    def remove_subscription(self, user_id, subscriber_id):
        c = self.connection.cursor()
        c.execute('DELETE FROM subscriptions '
                  'WHERE userId = ? AND subscriberId = ?', (user_id, subscriber_id))
        self.connection.commit()

    def get_subscriptions(self, subscriber_id):
        c = self.connection.cursor()
        c.execute('SELECT users.telegramName FROM subscriptions '
                  'INNER JOIN users ON subscriptions.userId = users.id '
                  'WHERE subscriberId = ?', (subscriber_id, ))
        result = map(lambda row: {'tg_name': row[0]}, c.fetchall())
        return list(result)

    def set_city(self, user_id, city_name):
        c = self.connection.cursor()
        c.execute('UPDATE users SET cityName = ? WHERE id = ?', (city_name, user_id))
        self.connection.commit()

    def get_city(self, user_id):
        c = self.connection.cursor()
        c.execute('SELECT cityName FROM users WHERE id = ?', (user_id,))
        city = list(map(lambda row: row[0], c.fetchall()))
        if city[0] is None:
            city = ['']
        return ' '.join(city)

    def set_introspect_timestamp(self, user_id, ts):
        c = self.connection.cursor()
        c.execute('UPDATE users SET introspectTimestamp = ? WHERE id = ?', (ts, user_id))
        self.connection.commit()
        
    def get_user_by_id(self, user_id):
        c = self.connection.cursor()
        c.execute('SELECT chatId FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        if result is not None:
            return {
                'chat_id': result[0]
            }
        return None

    def get_top_friend_events(self, user_id):
        c = self.connection.cursor()
        c.execute('SELECT users_events.eventId, COUNT(users.id) FROM users '
                  'INNER JOIN subscriptions '
                  'ON users.id = subscriptions.userId AND subscriptions.subscriberId = ? '
                  'INNER JOIN users_events ON users.id = users_events.userId '
                  'GROUP BY users_events.eventId '
                  'ORDER BY COUNT(users.id) DESC ', (user_id,))
        result = c.fetchall()
        return list(map(lambda row: {'event_id': row[0], 'count': row[1]}, result))

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('DROP TABLE IF EXISTS subscriptions')
    c.execute('DROP TABLE IF EXISTS users_events')
    c.execute('DROP TABLE IF EXISTS users')

    c.execute('CREATE TABLE users '
              '(id INTEGER PRIMARY KEY AUTOINCREMENT, timepadId INTEGER, chatId INTEGER, telegramName TEXT,'
              'email TEXT, token TEXT, cityName TEXT, introspectTimestamp TIMESTAMP)')
    c.execute('CREATE TABLE users_events '
              '(userId INTEGER, eventId INTEGER, PRIMARY KEY(userId, eventId),'
              'FOREIGN KEY(userId) REFERENCES users(id))')
    c.execute('CREATE TABLE subscriptions '
              '(userId INTEGER, subscriberId INTEGER, PRIMARY KEY(userId, subscriberId),'
              'FOREIGN KEY(userId) REFERENCES users(id),'
              'FOREIGN KEY(subscriberId) REFERENCES users(id))')


if __name__ == '__main__':
    init_db()
