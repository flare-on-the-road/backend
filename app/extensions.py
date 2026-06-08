from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flasgger import Swagger

db = SQLAlchemy()
cors = CORS()
migrate = Migrate()
swagger = Swagger()