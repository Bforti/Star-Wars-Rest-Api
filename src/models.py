from flask_sqlalchemy import SQLAlchemy # type: ignore

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    favoritos_planet = db.relationship('UPlanetFavorite', primaryjoin='User.id == UPlanetFavorite.user_id', backref='user', lazy=True)
    favoritos_people = db.relationship('UPeopleFavorite', backref='user', lazy=True)
  
    def __repr__(self):
        return f'<User {self.email}>'

    def serialize(self):
        return{
            "id":self.id,
            "email":self.email        }

class People(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=False, nullable=False)
    height = db.Column(db.String(10), nullable=True)
    weight = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    favoritos_character = db.relationship('UPeopleFavorite', backref='character', lazy=True)


    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "weight": self.weight,
            "gender": self.gender
        }

class Planets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=False, nullable=False)
    climate = db.Column(db.String(10), nullable=True)
    terrain = db.Column(db.String(10), nullable=True)
    resources = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    favoritos_planet = db.relationship('UPlanetFavorite', backref='planet', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "climate": self.climate,
            "terrain": self.terrain,
            "resources": self.resources
        }
    
class UPeopleFavorite(db.Model):
    __tablename__ = "UPeopleFavorite"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    people_id = db.Column(db.Integer, db.ForeignKey('people.id'))


    def __repr__(self):
        return '<UPeopleFavorite %r>' % self.id

    def serialize(self):
        result = People.query.filter_by(id=self.people_id).first()
        return {
            "id": self.id,
            "user_id": self.user_id,
            "people_id": result.serialize()["name"], 
        }
class UPlanetFavorite(db.Model):
    __tablename__ = "UPlanetFavorite"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    planets_id = db.Column(db.Integer, db.ForeignKey('planets.id'))

    def __repr__(self):
        return '<UPlanetFavorite %r>' % self.id

    def serialize(self):
        result = Planets.query.filter_by(id=self.planets_id).first()

        return {
            "id": self.id,
            "user_id": self.user_id,
            "planets_id": result.serialize()["name"],
        }
