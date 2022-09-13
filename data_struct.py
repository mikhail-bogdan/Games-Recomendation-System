from app import db

gameinfo_category = db.Table(
    "gameinfo_category",
    db.metadata,
    db.Column("appid", db.Integer, db.ForeignKey("games_info.appid")),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.category_id")),
)

gameinfo_genre = db.Table(
    "gameinfo_genre",
    db.metadata,
    db.Column("appid", db.Integer, db.ForeignKey("games_info.appid")),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.genre_id"))
)

users_games = db.Table(
    "users_games",
    db.metadata,
    db.Column("userid", db.Integer, db.ForeignKey("users.userid")),
    db.Column("appid", db.Integer, db.ForeignKey("games_info.appid"))
)

user_wishlisted = db.Table(
    "user_wishlisted",
    db.metadata,
    db.Column("userid", db.Integer, db.ForeignKey("users.userid")),
    db.Column("appid", db.Integer, db.ForeignKey("games_info.appid"))
)


class GameInfo(db.Model):
    __tablename__ = "games_info"

    appid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30, convert_unicode=True))
    detailed_description = db.Column(db.String(8192, convert_unicode=True))
    short_description = db.Column(db.String(512, convert_unicode=True))
    website = db.Column(db.String(128, convert_unicode=True))
    developers = db.Column(db.String(256, convert_unicode=True))
    publishers = db.Column(db.String(256, convert_unicode=True))
    # price_overview =
    categories = db.relationship(
        "Category", secondary=gameinfo_category)
    genres = db.relationship(
        "Genre", secondary=gameinfo_genre)

    # screenshots
    # release_date
    # background_raw

    def __repr__(self):
        return f"Game(id={self.appid!r}, name={self.name!r})"


class Category(db.Model):
    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32, ))


class Genre(db.Model):
    __tablename__ = "genres"

    genre_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32, convert_unicode=True))


class User(db.Model):
    __tablename__ = "users"

    userid = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(64, convert_unicode=True))
    name = db.Column(db.String(64, convert_unicode=True))
    games = db.relationship(
        "GameInfo", secondary=users_games)
    wishlisted = db.relationship(
        "GameInfo", secondary=user_wishlisted)


class Viewed(db.Model):
    __tablename__ = "viewed"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.userid"))
    appid = db.Column(db.Integer, db.ForeignKey("users.userid"))
    count = db.Column(db.Integer, default=0)


