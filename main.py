from website import create_app
from website import recreate_database
from flask_wtf.csrf import CSRFProtect


app = create_app()
csrf = CSRFProtect(app)

if __name__ == '__main__':
    # recreate_database(app)
    app.run(debug=True)
    