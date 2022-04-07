import waitress
import restApi

if __name__=="__main__":
    print("Starting server...")
    waitress.serve(restApi.app, host='0.0.0.0', port=5000)