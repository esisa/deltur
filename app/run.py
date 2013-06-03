import logging
logging.basicConfig()

from delturapp.app import app

if __name__ == '__main__':
    app.debug = True
    UPLOAD_FOLDER = 'upload'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.run(host='0.0.0.0')
