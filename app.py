from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
    <head><title>Agent Produits - Test</title></head>
    <body>
        <h1>🎉 Votre Agent Fonctionne !</h1>
        <p>L'application est maintenant en ligne.</p>
        <p>Version de test - Déploiement réussi !</p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Application en ligne'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

