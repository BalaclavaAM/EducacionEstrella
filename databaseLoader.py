from secrets import choice
import faker 
import pymssql 
import json

fake = faker.Faker('es_ES')

def connectionDatabase():
    """
    Access to config.json and return the connection
    """
    with open('config.json') as json_file:
        data = json.load(json_file)
        host = data['host']
        username = data['username']
        password = data['password']
        database = data['database']
        conn=pymssql.connect(host, username, password, database)
        return conn, conn.cursor(as_dict=True)
    
def poblateUserTable(cursor, conn):
    for x in range(0,5600):
        try:
            profile=fake.profile()
            username = profile['username']
            mail = profile['mail']
            password = fake.password()
            cursor.execute('INSERT INTO usuario (username, email, password) VALUES (%s, %s, %s)', (username, mail, password))
        except Exception as e:
            print(e)
    conn.commit()
    conn.close()
    
def poblatePostTable(cursor, conn):
    cursor.execute('SELECT idUser FROM usuario')
    userIds = cursor.fetchall()
    for x in range(0,2500):
        userId = choice(userIds)['idUser']
        postName = fake.sentence()
        postTags = ', '.join([fake.word() for i in range(0,3)])
        postContent = fake.text(max_nb_chars=200)
        try:
            print('Inserting post...' + str(x+1))
            cursor.execute('INSERT INTO post (idOwner, postName, postTags, postContent) VALUES (%s, %s, %s, %s)', (userId, postName, postTags, postContent))
        except Exception as e:
            print(e)
    conn.commit()
    conn.close()
    
conn, cursor = connectionDatabase()
poblatePostTable(cursor, conn)
        