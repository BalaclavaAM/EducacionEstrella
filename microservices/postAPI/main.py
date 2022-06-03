import json
from flask import Flask, Response, request

from pymongo import MongoClient
import waitress

app = Flask(__name__)

def getDatabase():
    CONNECTIONSTRING = "mongodb://127.0.0.1:27017/"
    client = MongoClient(CONNECTIONSTRING)
    
    return client['posts_db']

@app.route('/posts', methods=['GET', 'POST'])
def getPosts():
    try:
        if request.method == 'GET':
            posts = dbname.posts.find()
            return Response(json.dumps(posts), mimetype='application/json')
        elif request.method == 'POST':
            post = request.get_json()
            dbname.posts.insert_one(post)
            return Response(json.dumps(post), mimetype='application/json')
    except Exception as e:
        return Response(500, str(e))

@app.route('/posts/<id>', methods=['GET'])
def getPostById(id):
    try:
        posts = dbname.posts.find_one({'_id': id})
        return Response(200, json.dumps(posts))
    except Exception as e:
        return Response(500, str(e))
    
    
if __name__ == '__main__':
    dbname = getDatabase()
    waitress.serve(app, host='0.0.0.0', port=8081)