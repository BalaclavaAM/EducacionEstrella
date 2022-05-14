import json
from os import environ
import re
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen
from flask import Flask, Response, redirect, render_template, request, url_for
from jose import jwt
import pymssql
import logging
from logging.handlers import RotatingFileHandler
from authlib.integrations.flask_client import OAuth
from requests import session
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
rh = RotatingFileHandler('logs/restApi.log', maxBytes=10000, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s - %(lineno)d - %(funcName)s')
sh.setFormatter(formatter)
rh.setFormatter(formatter)

logger.addHandler(sh)
logger.addHandler(rh)

#RotateFileHandler
#FormatLogger

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

app = Flask(__name__)
app.secret_key = environ.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=environ.get("AUTH0_CLIENT_ID"),
    client_secret=environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

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
    "getUser": "SELECT * FROM usuario WHERE username = %s",
    "getFinanceFromUser": "SELECT * FROM informacionFinanciera WHERE idUser = %s",
    "insertInformacionFinanciera": "INSERT INTO informacionFinanciera ([idUser],[banco],[cuenta],[tipoCuenta]) VALUES (%d,%s,%s,%s)",
    "updateInformacionFinanciera": "UPDATE informacionFinanciera SET [banco] = %s, [cuenta] = %s, [tipoCuenta] = %s WHERE idUser = %d",
}

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
 
def checkMailForm(email:str):
    if(re.fullmatch(regex, email)):
        return True
    return False

def getTokenAuth0():
    headers = {'content-type': 'application/json'}
    body = {'client_id':environ.get("AUTH0_CLIENT_ID"), 'client_secret': environ.get("AUTH0_CLIENT_SECRET"),"audience":"172.24.41.170:8080","grant_type":"client_credentials"}
    domain = environ.get("AUTH0_DOMAIN")
    response = requests.post(f'{domain}/oauth/token', headers=headers, data=json.dumps(body))
    return response.json()

def validateTokenAuth0(access_token:str, token_type:str='Bearer')->bool:
    retorno = False
    try:
        domain = environ.get("AUTH0_DOMAIN")
        jsonurl = urlopen(f"{domain}/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(access_token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    access_token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience='172.24.41.170:8080',
                    issuer=domain+"/"
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired",
                                "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    "please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401)

            retorno = True
        raise AuthError({"code": "invalid_header",
                        "description": "Unable to find appropriate key"}, 401)
    except Exception as e:
        logger.error(e)
    finally:
        return retorno
    

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
            logger.info(f"Query: {query}")
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
            logger.info(f"Query: {query}")
            logger.info(f"Params: {params}")
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
            logger.info(f"Query: {query}")
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
            logger.info(f"Query: {query}")
            logger.info(f"Params: {params}")
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
            logger.info(f"Query: {query}")
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
            logger.info(f"Query: {query}")
            logger.info(f'Params: {params}')
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
            logger.info(f"Query: {query}")
            logger.info(f'Params: {params}')
            filasAfectadas=cursor.rowcount
            status = 201
            retorno = {'filasAfectadas': filasAfectadas}
            conn.commit()
        elif request.method == 'GET':
            query = QUERYS['getAllCursos']
            cursor.execute(query)
            logger.info(f'Query: {query}')
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
            logger.info(f'Query: {query}')
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
            logger.info(f'Query: {query}')
            logger.info(f'params: {params}')
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
            logger.info(f'Query: {query}')
            logger.info(f'params: {params}')
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
    

@app.route("/login")
def login():
    status = 500
    retorno = {}
    conn, cursor = connectionDatabase()
    try:
        content = request.json
        requiredKeys = ['username', 'password']
        for key in requiredKeys:
            if key not in content:
                status = 400
                raise Exception('Faltan datos', key)
        user = content['username']
        password = content['password']
        query = QUERYS['getUser']
        cursor.execute(query, (user))
        logger.info(f'Query: {query}')
        logger.info(f'Params: {(user,)}')
        result = cursor.fetchall()
        validPassword = False
        for user in result:
            #Remove trailing spaces from
            if user['password'].strip() == password:
                validPassword = True
        if not validPassword:
            status = 401
            raise Exception('Usuario o contraseña incorrectos')
        retorno['token']=getTokenAuth0()
        retorno['idUser']=result['idUser']
        status = 200
    except Exception as e:
        logger.error(f'Error: {str(e)}')
        retorno['error']=str(e)
    finally:
        conn.close()
        return Response(json.dumps(retorno), status, mimetype='application/json')
    
@app.route('/finance', methods=['GET', 'PUT', 'PATCH'])
def financeManagement():

    conn, cursor = connectionDatabase()
    status = 500
    retorno = []
    
    #get token from header
    try:
        token = request.headers.get('authorization')
        if token is None: raise Exception('No token provided')
        validToken = validateTokenAuth0(token)
        if not validToken: raise Exception('Invalid token: ' + str(validToken))
        if request.method == 'GET':
            query = QUERYS['getFinanceFromUser']
            content = request.json
            requiredKeys = ['idUser']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['idUser'])
            cursor.execute(query, params)
            logger.info(f'Query: {query}')
            retorno = cursor.fetchall()
            status = 200
        elif request.method == 'PUT':
            query = QUERYS['insertInformacionFinanciera']
            content = request.json
            requiredKeys = ['idUser', 'banco', 'cuenta', 'tipoCuenta']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['idUser'], content['banco'], content['cuenta'], content['tipoCuenta'])
            logger.info(f'Query: {query}')
            logger.info(f'params: {params}')
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            status = 201
            retorno = {'filasAfectadas': filasAfectadas}
            conn.commit()
        elif request.method == 'PATCH':
            query = QUERYS['updateInformacionFinanciera']
            content = request.json
            requiredKeys = ['idUser', 'banco', 'cuenta', 'tipoCuenta']
            for key in requiredKeys:
                if key not in content:
                    status = 400
                    raise Exception('Faltan datos', key)
            params = (content['banco'], content['cuenta'], content['tipoCuenta'], content['idUser'])
            logger.info(f'Query: {query}')
            logger.info(f'params: {params}')
            cursor.execute(query, params)
            filasAfectadas=cursor.rowcount
            logger.info(f'filasAfectadas: {filasAfectadas}')
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

        
    

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
    
@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))