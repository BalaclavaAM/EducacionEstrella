import json
import re
from flask import Flask, Response, request
import pymssql

app = Flask(__name__)

QUERYS= {
    "obtenerallusers": "SELECT * FROM usuario",
    "insertUser": "INSERT INTO usuario (username, password, email) VALUES (%s, %s, %s)",
    "insertUserWRol": "INSERT INTO usuario (username, password, email, idRol) VALUES (%s, %s, %s, %d)",
    "getAllRoles": "SELECT * FROM usuarioRoles",
    "insertRol": "INSERT INTO usuarioRoles (nameRol) VALUES (%s)",
    "insertPost": "INSERT INTO post (titulo, postName, postTags, postContent, idOwner) VALUES (%s, %s, %s, %s, %d)",
    "getAllPosts": "SELECT * FROM post",
    "getAllCursos": "SELECT * FROM curso",
    "insertCurso": "INSERT INTO curso (nombreCurso, descripcionCurso, userPromotor, fechaCurso) VALUES (%s, %s, %d, %s)",
    "getAllMarketplace": "SELECT idCurso, isActive FROM marketplace",
    "insertMarketplace": "INSERT INTO marketplace (idCurso, isActive) VALUES (%d, %d)",
    "updateMarketplace": "UPDATE marketplace SET isActive = %d WHERE idCurso = %d",
}

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
 
def checkMailForm(email:str):
    if(re.fullmatch(regex, email)):
        return True
    return False

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


@app.route('/usuario', methods=['POST', 'GET'])
def userManagement():
    #if request is GET:
    status = 500
    retorno = []
    conn, cursor = connectionDatabase()
    try:
        if request.method == 'GET':
            query = QUERYS['obtenerallusers']
            cursor.execute(query)
            response = cursor.fetchall()
            status = 200
            retorno = response
        elif request.method == 'POST':
            necesaryItems = ['username', 'password', 'email']
            content=request.json
            for key in necesaryItems:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            #check regex email
            if not(checkMailForm(content['email'])):
                status = 400
                raise Exception('Email invalido')
            query = QUERYS['insertUser']
            params = (content['username'], content['password'], content['email'])
            if 'rol' in content:
                query = QUERYS['insertUserWRol']
                params = (content['username'], content['password'], content['email'], content['rol'])
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            retorno = {'filasAfectadas': filasAfectadas}
            status=201
            conn.commit()
    except Exception as e:
        conn.rollback()
        retorno = json.dumps({'error':str(e)})
    finally:
        conn.close()
        return Response(json.dumps(retorno), status, mimetype='application/json')
    
@app.route('/roles', methods=['GET', 'POST'])
def rolesManagement():
    status = 500
    retorno = []
    conn, cursor = connectionDatabase()
    try:
        if request.method == 'GET':
            query = QUERYS['getAllRoles']
            cursor.execute(query)
            response = cursor.fetchall()
            status = 200
            retorno = response
        elif request.method == 'POST':
            necesaryItems = ['name']
            content=request.json
            for key in necesaryItems:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            #check regex email
            query = QUERYS['insertRol']
            params = (content['name'])
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            retorno = {'filasAfectadas': filasAfectadas}
            status = 201
            conn.commit()
    except Exception as e:
        conn.rollback()
        retorno = json.dumps({'error':str(e)})
    finally:
        conn.close()
        return Response(json.dumps(retorno), status, mimetype='application/json')
    
@app.route('/post', methods=['POST', 'GET'])
def postManagement():
    conn, cursor = connectionDatabase()
    status = 500
    retorno = []
    try:
        if request.method == 'GET':
            query = QUERYS['getAllPosts']
            cursor.execute(query)
            response = cursor.fetchall()
            status = 200
            retorno = response
        elif request.method == 'POST':
            content = request.json
            query = QUERYS['insertPost']
            requiredKeys = ['postContent', 'postName', 'postTags', 'titulo', 'idOwner']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['titulo'], content['postName'], content['postTags'], content['postContent'], content['idOwner'])
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            status = 201
            retorno = {'filasAfectadas': filasAfectadas}
            conn.commit()
    except Exception as e:
        conn.rollback()
        retorno = json.dumps({'error':str(e)})
        print("Error: ", e)
    finally:
        conn.close()
        return Response(json.dumps(retorno), status, mimetype='application/json')

@app.route('/curso', methods=['POST', 'GET'])
def cursoManagement():
    conn, cursor = connectionDatabase()
    status = 500 
    retorno = []
    try:
        if request.method == 'POST':
            content = request.json
            query = QUERYS['insertCurso']
            requiredKeys = ['nombreCurso', 'descripcionCurso', 'userPromotor', 'fechaCurso']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['nombreCurso'], content['descripcionCurso'], content['userPromotor'], content['fechaCurso'])
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            status = 201
            retorno = {'filasAfectadas': filasAfectadas}
            conn.commit()
        elif request.method == 'GET':
            query = QUERYS['getAllCursos']
            cursor.execute(query)
            retorno = cursor.fetchall()
            for curso in retorno:
                curso['fechaCurso']=curso['fechaCurso'].strftime('%Y-%m-%d')
            status = 200
    except Exception as e:
        print("Error: ", e)
        retorno = json.dumps({'error':str(e)})
        conn.rollback()
    finally:
        conn.close()
        return Response(json.dumps(retorno), status, mimetype='application/json')
    
@app.route('/marketplace', methods=['GET', 'PUT', 'PATCH'])
def marketplace():
    conn, cursor = connectionDatabase()
    status = 500
    retorno = []
    try:
        if request.method == 'GET':
            query = QUERYS['getAllMarketplace']
            cursor.execute(query)
            retorno = cursor.fetchall()
            status = 200
        elif request.method == 'PUT':
            query = QUERYS['insertMarketplace']
            content = request.json
            requiredKeys = ['idCurso', 'isActive']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['idCurso'], content['isActive'])
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            status = 201
            retorno = {'filasAfectadas': filasAfectadas}
            conn.commit()
        elif request.method == 'PATCH':
            query = QUERYS['updateMarketplace']
            content = request.json
            requiredKeys = ['idCurso', 'isActive']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['idCurso'], content['isActive'])
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            status = 201
            retorno = {'filasAfectadas': filasAfectadas}
            conn.commit()
    except Exception as e:
        print("Error: ", e)
        retorno = json.dumps({'error':str(e)})
        conn.rollback()
    finally:
        conn.close()
        return Response(json.dumps(retorno), status, mimetype='application/json')