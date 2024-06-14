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








@app.route("/users", methods=["POST"])
def create():
    data = request.get_json()
    email = data["email"]
    
    repetido = User.query.filter_by(email=email).first()
    if repetido: 
        return jsonify({"error":"correo registrado"}), 400
    
    password = data["password"]

    user = User(email=email,password=password,is_active=True)
    
    db.session.add(user)
    db.session.commit()   
    return jsonify({"mensaje":"registro exitoso"}),201



@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    all_u = []

    for user in users:
        serialized_user = user.serialize()
        all_u.append(serialized_user)

    return jsonify(all_u), 200


@app.route('/users/favorites', methods=['GET'])
def get_list_favorites():
    data=request.get_json()
    email = data["email"]
    user_query = User.query.filter_by(email=email).first()
    user_id=user_query.id

    favorite_people = UPeopleFavorite.query.filter_by(user_id=user_id).all()
    favorite_planet = UPlanetFavorite. query.filter_by(user_id=user_id).all()
    results_character = list(map(lambda item: item.serialize(), favorite_people))
    results_planet = list(map(lambda item: item.serialize(), favorite_planet))
    
    if results_character == [] and results_planet == []:
        return jsonify({"msg": "favorites not found"}), 404
    response_body = {
        "msg": "ok",
        "results": [results_character, results_planet],
        }
    return jsonify(response_body), 200




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





@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_fav_character_to_user(people_id):
    data = request.get_json()
    email = data.get("email")  # Utiliza get para evitar errores si 'email' no está presente
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    character = People.query.get(people_id)
    if not character:
        return jsonify({"error": "Character not found"}), 404

    # Verifica si el usuario ya tiene este personaje como favorito
    if UPeopleFavorite.query.filter_by(user_id=user.id, people_id=people_id).first():
        return jsonify({"msg": "Character already exists in favorites"}), 400

    # Agrega el personaje como favorito para el usuario
    favorite_character = UPeopleFavorite(people_id=people_id, user_id=user.id)
    db.session.add(favorite_character)
    db.session.commit()
    
    return jsonify({"msg": "Character added to favorites"}), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_fav_planet_to_user(planet_id):
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    planet = Planets.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    # Verifica si el usuario ya tiene este planeta como favorito
    if UPlanetFavorite.query.filter_by(user_id=user.id, planet_id=planet_id).first():
        return jsonify({"msg": "Planet already exists in favorites"}), 400

    # Agrega el planeta como favorito para el usuario
    favorite_planet = UPlanetFavorite(planet_id=planet_id, user_id=user.id)
    db.session.add(favorite_planet)
    db.session.commit()
    
    return jsonify({"msg": "Planet added to favorites"}), 200





@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    data=request.get_json()
    email = data["email"]
    user_query = User.query.filter_by(email=email).first()
    user_id = user_query.id
    planet_query = Planets.query.filter_by(id=planet_id).first()
    if planet_query is None:
        return ({"msg": "the planet doesn't exist"}), 400
    else:
        planet_query = UPlanetFavorite.query.filter_by(planet_id=planet_id, user_id=user_id).first()
    if planet_query:
        db.session.delete(planet_query)
        db.session.commit()
        return jsonify({"msg": "planet was successfully deleted"}), 200
    else:
        return jsonify({"msg": "planet not found"}), 404 
    

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_people(people_id):
    data=request.get_json()
    email = data["email"]
    user_query = User.query.filter_by(email=email).first()
    user_id = user_query.id
    people_query = People.query.filter_by(id=people_id).first()
    if people_query is None:
        return ({"msg": "the character doesn't exist"}), 400
    else:
        people_query = UPeopleFavorite.query.filter_by(people_id=people_id, user_id=user_id).first()
    if people_query:
        db.session.delete(people_query)
        db.session.commit()
        return jsonify({"msg": "character was successfully deleted"}), 200
    else:
        return jsonify({"msg": "character not found"}), 404 

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)