import json
import os
import waitress
import restApi



if __name__=="__main__":
    with open('config.json') as json_file:
        data = json.load(json_file)
        os.environ['AUTH0_CLIENT_ID'] = data['auth0']['client_id']
        os.environ['AUTH0_CLIENT_SECRET'] = data['auth0']['client_secret']
        os.environ['AUTH0_DOMAIN'] = data['auth0']['domain']
    print("Starting server... in port 8080")
    waitress.serve(restApi.app, host='0.0.0.0', port=8080)