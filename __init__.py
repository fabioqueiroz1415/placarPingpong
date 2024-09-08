from app import *

if __name__ == '__main__':
    if not os.getenv('WERKZEUG_RUN_MAIN'):
        generate_qr_rota("/links").show()
    app.run(host='0.0.0.0', debug=True, threaded=True)