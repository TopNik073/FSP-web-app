import logging
import os
from flask import Flask
from werkzeug.security import generate_password_hash
from blueprints import blueprints
from common import *
from dotenv import load_dotenv
from DB.user import User

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

for blueprint in blueprints:
    app.register_blueprint(blueprint[0], url_prefix=blueprint[1])

if __name__ == "__main__":
    user = User(email=os.environ.get("ADMIN_EMAIL"), password=generate_password_hash(os.environ.get("ADMIN_PASSWORD")), is_verified=True, role="ADMIN")
    if user.get() is None:
        user.add()
        logger.info("Admin user was created")

    app.run(host="0.0.0.0", port=5000)
