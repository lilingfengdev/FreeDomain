from app import create_app, db
from app.models.user import User
from app.models.domain import Domain, Subdomain
from app.models.card import Card

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Domain': Domain, 'Subdomain': Subdomain, 'Card': Card}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
