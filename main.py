from website import create_app
from website import recreate_database

# import cryptography

app = create_app()

if __name__ == '__main__':
    recreate_database(app)
    app.run(debug=True)