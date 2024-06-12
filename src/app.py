"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, UPeopleFavorite, UPlanetFavorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    all_u = []

    for user in users:
        serialized_user = user.serialize()
        all_u.append(serialized_user)

    return jsonify(all_u), 200

@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    serialized_people_list = list(map(lambda People: People.serialize(), people))
    
    return jsonify(serialized_people_list), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get_or_404(people_id)
    
    return jsonify(person.serialize()), 200

@app.route('/people', methods=['POST'])
def add_person():
    request_body = request.get_json()
    person = People(name=request_body["name"], height=request_body["height"], weight=request_body["weight"], gender=request_body["gender"])
    db.session.add(person)
    db.session.commit()

    return f"The person {request_body['name']} was added to the database", 200

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planets.query.all()
    serialized_planets_list = list(map(lambda Planets: Planets.serialize(), planets))
    
    return jsonify(serialized_planets_list), 200

@app.route('/planets', methods=['POST'])
def add_planet():

    request_body = request.get_json()
    planet = Planets(name=request_body["name"], climate=request_body["climate"], terrain=request_body["terrain"], resources=request_body["resources"])
    db.session.add(planet)
    db.session.commit()

    return f"The planet {request_body['name']} was added to the database", 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planets.query.get_or_404(planet_id)
    
    return jsonify(planet.serialize()), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = request.json.get('user_id')  

    if user_id is None:
        return jsonify({"error": "User ID is required."}), 400
    
    user = User.query.get(user_id)

    if user is None:
        return jsonify({"error": "User not found."}), 404
    
    favorites = user.favorites
    
    serialized_favorites = [favorite.serialize() for favorite in favorites]
    
    return jsonify(serialized_favorites), 200

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    user_id = request.json.get('user_id')

    user = User.query.get(user_id)
    person = People.query.get(people_id)

    favorite_relation = UPeopleFavorite(user_id=user_id, people_id=people_id)
    db.session.add(favorite_relation)
    db.session.commit()

    return jsonify({"message": f"Added {person.name} to favorites for user {user.name}"}), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planets(planet_id):
    user_id = request.json.get('user_id')

    user = User.query.get(user_id)
    planet = Planets.query.get(planet_id)

    favorite_relation = UPlanetFavorite(user_id=user_id, planet_id=planet_id)
    db.session.add(favorite_relation)
    db.session.commit()

    return jsonify({"message": f"Added {planet.name} to favorites for user {user.name}"}), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.json.get('user_id')  
    
    if user_id is None:
        return jsonify({"error": "User ID is required."}), 400
    
    user = User.query.get(user_id)
    
    if user is None:
        return jsonify({"error": "User not found."}), 404
    
    favorite_planet = Planets.query.get(planet_id)
    
    if favorite_planet is None:
        return jsonify({"error": "Favorite planet not found."}), 404
    
    if favorite_planet not in user.planet_favorites:
        return jsonify({"error": "Planet is not a favorite of the user."}), 400
    
    user.planet_favorites.remove(favorite_planet)
    db.session.commit()
    
    return jsonify({"message": f"Favorite planet {favorite_planet.name} deleted for user {user.name}"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user_id = request.json.get('user_id')  
    
    if user_id is None:
        return jsonify({"error": "User ID is required."}), 400

    user = User.query.get(user_id)

    if user is None:
        return jsonify({"error": "User not found."}), 404
    
    favorite_person = People.query.get(people_id)
    
    if favorite_person is None:
        return jsonify({"error": "Favorite person not found."}), 404
    
    if favorite_person not in user.people_favorites:
        return jsonify({"error": "Person is not a favorite of the user."}), 400
    
    user.people_favorites.remove(favorite_person)
    db.session.commit()
    
    return jsonify({"message": f"Favorite person {favorite_person.name} deleted for user {user.name}"}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)