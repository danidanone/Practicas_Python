from flask import Flask
from routes import init_api_routes
from db import Base, engine
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

Base.metadata.create_all(engine)

init_api_routes(app)

if __name__ == '__main__':
    app.run(debug=True)