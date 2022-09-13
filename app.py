import datetime
import random
import time
from itertools import islice
from math import sqrt

from flask_sqlalchemy import SQLAlchemy
from requests import get
from flask import Flask, jsonify, request, session, redirect
from markupsafe import escape
from jinja2 import Environment, PackageLoader, select_autoescape
from matplotlib import pyplot as plt
from sklearn import cluster


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
sess = db.session

from data_struct import *

db.create_all()


env = Environment(
    loader=PackageLoader("app"),
    autoescape=select_autoescape()
)

main_template = env.get_template("main.html")
gamepage_template = env.get_template("game_page.html")
userpage_template = env.get_template("user_page.html")
login_template = env.get_template("login.html")
library_template = env.get_template("library.html")


steamapi_key = "47638972FFB44B0D63A990A1E37AAEEA"

keys = ['name', 'detailed_description', 'short_description', 'header_image',
        'website', 'developers', 'publishers', 'categories', 'genres',
        'screenshots', 'release_date', 'background_raw']

users = [
    'misha_bogdan', 'Schnubbl', 'HKNI', 'pepper_mustard',
    'kirill20122002', 'sshKEYnoSKytiME', 'mih1121', 'Dar-ling',
    '0xzaphod42', '2Under_taker6', 'profile198381',
]

user_ids = [
    '76561198105889758', '76561198127499656',
    '76561198222479576', '76561198138350832',
    '76561198247364610',
]

genres = {
    "Action": 1, "Strategy": 2, "Role-Playing": 3,
    "Casual": 4, "Racing": 9, "Simulation": 28
}

metrics_ids = [1, 2, 3, 4, 9, 28]
users_metrics = {}


@app.route('/')
def main():
    games = (
        sess.query(GameInfo)
        .all()
    )

    return main_template.render(games=games, name=session.get('login', None))


@app.route("/login", methods=['GET', 'POST'])
@app.route("/login/", methods=['GET', 'POST'])
def login_page():
    data = request.form
    if len(data) == 0:
        return login_template.render()
    session['login'] = data['login']
    user = (
        sess.query(User)
            .filter(User.username == session['login'])
            .one_or_none()
    )

    if user is None:
        user = User(username=session['login'], name=session['login'])
        sess.add(user)
        sess.commit()
        user = (
            sess.query(User)
                .filter(User.username == session['login'])
                .one_or_none()
        )

    session['id'] = user.userid

    return redirect("/")


@app.route("/logout")
@app.route("/logout/")
def logout_page():
    if 'login' in session:
        session.pop('login', None)
        session.pop('id', None)
    return redirect(request.referrer)


@app.route("/library")
@app.route("/library/")
def library_page():
    if 'login' not in session:
        return redirect("/login")

    user = (
        sess.query(User)
        .filter(User.username == session['login'])
        .one_or_none()
    )

    return library_template.render(user=user)


@app.route('/game/<appid>')
@app.route('/game/<appid>/')
def game_page(appid):
    game = (
        sess.query(GameInfo)
        .filter(GameInfo.appid == int(escape(appid)))
        .one_or_none()
    )

    if game is None:
        return "Игра не существует"

    bought = False
    wishlisted = False

    if 'login' in session:
        user = (
            sess.query(User)
                .filter(User.userid == session['id'])
                .one_or_none()
        )
        bought = game in user.games
        wishlisted = game in user.wishlisted

        viewed = (
            sess.query(Viewed)
            .filter(Viewed.userid == session['id'])
            .filter(Viewed.appid == appid)
            .one_or_none()
        )

        if viewed is None:
            viewed = Viewed(userid=session['id'], appid=appid)
            sess.add(viewed)
            sess.commit()

        viewed.count = viewed.count + 1
        sess.add(viewed)
        sess.commit()

    return gamepage_template.render(game=game, bought=bought, wishlisted=wishlisted, name=session.get('login', None))


@app.route('/u/<userid>')
@app.route('/u/<userid>/')
def user_page(userid):
    userid = escape(userid)

    try:
        userid = int(userid)

        user = (
            sess.query(User)
            .filter(User.userid == int(escape(userid)))
            .one_or_none()
        )
    except:
        user = (
            sess.query(User)
            .filter(User.username == escape(userid))
            .one_or_none()
        )

    if user is None:
        return "Пользователь не существует"

    return userpage_template.render(user=user)


@app.route('/buy/<appid>', methods=['POST'])
def buy_game(appid):
    if 'login' not in session:
        return jsonify({'bought': False})

    user = (
        sess.query(User)
        .filter(User.userid == session['id'])
        .one_or_none()
    )

    game = (
        sess.query(GameInfo)
        .filter(GameInfo.appid == appid)
        .one_or_none()
    )

    user.games.append(game)
    sess.add(user)
    sess.commit()

    return jsonify({'bought': True})


@app.route('/revert/<appid>', methods=['POST'])
def revert_game(appid):
    if 'login' not in session:
        return jsonify({'bought': True})

    user = (
        sess.query(User)
            .filter(User.userid == session['id'])
            .one_or_none()
    )

    game = (
        sess.query(GameInfo)
            .filter(GameInfo.appid == appid)
            .one_or_none()
    )

    user.games.remove(game)
    sess.add(user)
    sess.commit()

    return jsonify({'bought': False})


@app.route('/wishlist/<appid>', methods=['POST'])
def wishlist(appid):
    data = request.json
    user = (
        sess.query(User)
            .filter(User.userid == session['id'])
            .one_or_none()
    )
    game = (
        sess.query(GameInfo)
            .filter(GameInfo.appid == appid)
            .one_or_none()
    )
    if data['state']:
        user.wishlisted.append(game)
        ret = True
    else:
        user.wishlisted.remove(game)
        ret = False
    sess.add(user)
    sess.commit()
    return jsonify({'state': ret})


def get_app_info(appid):
    data = None
    while data is None:
        data = get(f"https://store.steampowered.com/api/appdetails?appids={appid}").json()
        if data is None:
            print("sleep")
            time.sleep(random.randrange(60, 120))

    data = data[str(appid)]

    if not data['success']:
        return None

    data = data['data']
    app_info = {}

    for key in keys:
        if key not in data.keys():
            return None
        app_info[key] = data[key]

    return app_info


def get_user_apps(userid):
    data = get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={steamapi_key}&steamid={userid}&include_appinfo=true&include_played_free_games=true&appids_filter=").json()

    data = data['response']['games']

    i = 0
    games = []

    for app in data:
        i = i + 1
        print(i)

        game_info = add_game_to_database(app['appid'])
        if game_info is None:
            continue
        games.append(game_info)

    if len(games) > 0:
        user = (
            sess.query(User)
            .filter(User.userid == userid)
            .one_or_none()
        )
        user.games = games

        sess.add(user)
        sess.commit()


def get_all_games_ids_in_database():
    ids = []

    for row in sess.query(GameInfo.appid).all():
        ids.append(row.appid)

    return ids


def get_user_data(user_id):
    data = get(f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steamapi_key}&steamids={user_id}").json()
    data = data['response']['players'][0]

    user = (
        sess.query(User)
        .filter(User.userid == user_id)
        .one_or_none()
    )

    if user is not None:
        return user

    last = data['profileurl'].rfind('/')
    first = data['profileurl'].rfind('/', 0, last)

    user = User(
        userid=user_id,
        username=data['profileurl'][first + 1:last],
        name=data['personaname']
    )

    save_profile_image(user_id, data['avatarfull'])

    sess.add(user)
    sess.commit()


def save_profile_image(user_id, url):
    response = get(url)
    file = open(f"./static/profile_images/{user_id}.jpg", "wb")
    file.write(response.content)
    file.flush()
    file.close()


def add_game_to_database(appid):
    gameinfo = (
        sess.query(GameInfo)
        .filter(GameInfo.appid == appid)
        .one_or_none()
    )

    if gameinfo is not None:
        return gameinfo

    appinfo = get_app_info(appid)

    if appinfo is None:
        return None
    # app_info['playtime_forever'] = app['playtime_forever']

    categories = []
    for category_info in appinfo['categories']:
        categories.append(add_category_to_database(category_info))

    genres = []
    for genre_info in appinfo['genres']:
        genres.append(add_genre_to_database(genre_info))

    gameinfo = GameInfo(
        appid=appid,
        name=appinfo['name'],
        detailed_description=appinfo['detailed_description'],
        short_description=appinfo['short_description'],
        website=appinfo['website'],
        developers=str(appinfo['developers']),
        publishers=str(appinfo['publishers']),
        categories=categories,
        genres=genres
    )

    save_header_image(appid, appinfo['header_image'])

    sess.add(gameinfo)
    sess.commit()

    return gameinfo


def save_header_image(appid, url):
    response = get(url)
    file = open(f"./static/game_images/{appid}.jpg", "wb")
    file.write(response.content)
    file.flush()
    file.close()


def add_category_to_database(category_info):
    category = (
        sess.query(Category)
        .filter(Category.category_id == category_info['id'])
        .one_or_none()
    )

    if category is not None:
        return category

    category = Category(
        category_id=category_info['id'],
        name=category_info['description']
    )

    sess.add(category)
    sess.commit()

    return category


def add_genre_to_database(genre_info):
    genre = (
        sess.query(Genre)
        .filter(Genre.genre_id == genre_info['id'])
        .one_or_none()
    )

    if genre is not None:
        return genre

    genre = Genre(
        genre_id=genre_info['id'],
        name=genre_info['description']
    )

    sess.add(genre)
    sess.commit()

    return genre


def get_user_id(username):
    data = get(
        f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={steamapi_key}&vanityurl={username}").json()
    return data['response']['steamid']


def calculate_metric(userid):
    user = (
        sess.query(User)
        .filter(User.userid == userid)
        .filter()
        .one_or_none()
    )

    metric_g = [0 for i in range(6)]
    metric_w = [0 for i in range(6)]
    metric_v = [0 for i in range(6)]

    for game in user.games:
        for i in range(len(metric_g)):
            for genre in game.genres:
                if genre.genre_id == metrics_ids[i]:
                    metric_g[i] = metric_g[i] + 1
    if len(user.games) > 0:
        for i in range(6):
            metric_g[i] = metric_g[i] / len(user.games)

    for game in user.wishlisted:
        for i in range(len(metric_w)):
            for genre in game.genres:
                if genre.genre_id == metrics_ids[i]:
                    metric_w[i] = metric_w[i] + 1
    if len(user.wishlisted) > 0:
        for i in range(6):
            metric_w[i] = metric_w[i] / len(user.wishlisted)

    viewed = (
        sess.query(Viewed)
        .filter(Viewed.userid == userid)
        .all()
    )

    total_views = 0
    for view in viewed:
        game = (
            sess.query(GameInfo)
            .filter(GameInfo.appid == view.appid)
            .one_or_none()
        )
        for i in range(len(metric_v)):
            for genre in game.genres:
                if genre.genre_id == metrics_ids[i]:
                    metric_v[i] = metric_v[i] + view.count
        total_views = total_views + view.count
    if total_views > 0:
        for i in range(6):
            metric_v[i] = metric_v[i] / total_views

    for i in range(6):
        metric_g[i] = (metric_g[i] + metric_w[i] + metric_v[i]) / 3

    return metric_g



for user in users:
#    user_ids.append(str(get_user_id(user)))
    pass

for userid in user_ids:
#    get_user_data(userid)
#    get_user_apps(userid)
    pass


users_data = (
    sess.query(User)
    .all()
)

for user in users_data:
    users_metrics[user.name] = calculate_metric(user.userid)

user_names = [user.name for user in users_data]

metrics = list(users_metrics.values())
action = [users_metrics[user_name][0] for user_name in user_names]
strategy = [users_metrics[user_name][1] for user_name in user_names]
rpg = [users_metrics[user_name][2] for user_name in user_names]
casual = [users_metrics[user_name][3] for user_name in user_names]
racing = [users_metrics[user_name][4] for user_name in user_names]
simulation = [users_metrics[user_name][5] for user_name in user_names]
colors = ['red', 'gold', 'blue', 'green', 'orange',
         'yellow', 'magenta', 'pink', 'gray', 'cyan',
         'brown', 'silver', 'black', ]

data = cluster.OPTICS(metric='euclidean', min_samples=2, max_eps=0.2).fit(metrics)
data = data.labels_.astype(int)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

for i in range(len(users_data)):
    ax.scatter(action[i], strategy[i], rpg[i], s=10, color=colors[data[i]])
    ax.text(action[i], strategy[i], rpg[i], user_names[i], zdir='x')
ax.set_xlabel('action')
ax.set_ylabel('strategy')
ax.set_zlabel('role-playing')

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

for i in range(len(users_data)):
    ax.scatter(casual[i], racing[i], simulation[i], s=10, color=colors[data[i]])
    ax.text(casual[i], racing[i], simulation[i], user_names[i], zdir='x')
ax.set_xlabel('casual')
ax.set_ylabel('racing')
ax.set_zlabel('simulation')

plt.show()


def get_neighbours(data, num):
    result = []
    for i in range(len(data)):
        if data[i] == num:
            result.append(i)
    return result


def distance(a, b):
    sum = 0
    for i in range(len(a)):
        sum = sum + (a[i] - b[i]) ** 2
    return sqrt(sum)


@app.route("/get")
@app.route("/get/")
def get_games():
    users_data = (
        sess.query(User)
            .all()
    )

    for user in users_data:
        users_metrics[user.name] = calculate_metric(user.userid)

    user_names = [user.name for user in users_data]
    metrics = list(users_metrics.values())

    data = cluster.OPTICS(metric='euclidean', min_samples=2, max_eps=0.2).fit(metrics).labels_.astype(int)

    me = (
        sess.query(User)
        .filter(User.userid == session['id'])
        .one_or_none()
    )

    games = []

    me_i = -1
    for i in range(len(user_names)):
        if me.name == user_names[i]:
            me_i = i
            break

    me_cl = data[me_i]

    if me_cl == -1:
        min_i = -1
        min_d = 1000000000
        for i in range(len(user_names)):
            dist = distance(metrics[i], metrics[me_i])
            if i != me_i and dist < min_d:
                min_d = dist
                min_i = i
        user = (
            sess.query(User)
                .filter(User.name == user_names[min_i])
                .one_or_none()
        )

        i = 0
        while i < 10 and len(user.games) > 0:
            game = random.choice(user.games)
            games.append(game)
            user.games.remove(game)
            i = i + 1
        return main_template.render(games=games, name=session.get('login', None))

    nums = get_neighbours(data, me_cl)


    i = 0

    for num in nums:
        if num != me_i:
            user = (
                sess.query(User)
                .filter(User.name == user_names[i])
                .one_or_none()
            )

            while i < 10 and len(user.games) > 0:
                game = random.choice(user.games)
                games.append(game)
                user.games.remove(game)
                i = i + 1

    return main_template.render(games=games, name=session.get('login', None))



if __name__ == '__main__':
    app.run()
