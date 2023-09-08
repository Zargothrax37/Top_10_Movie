import os
from flask import Flask, render_template, redirect, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = "INSERT_KEY_HERE"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top_10_movie.db"
Bootstrap5(app)
db.init_app(app)


# Create db in Sqlite
class Movie10(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.Text, nullable=False)


if not os.path.exists('top_10_movie.db'):
    with app.app_context():
        db.create_all()


# Create a form to update rating and review
class EditFrom(FlaskForm):
    new_rating = StringField("Your rating out of 10")
    new_review = StringField("Your Review")
    submit = SubmitField("submit")
    new_movie = StringField("Please provide the name of a movie", validators=[DataRequired()])


# Read db file and passes it to home page
@app.route("/")
def home():
    try:
        with app.app_context():
            movie_data = Movie10.query.order_by(Movie10.rating.asc()).all()
            for i, movie in enumerate(movie_data):
                movie.ranking = len(movie_data) - i
        return render_template("index.html",
                               movie=movie_data)
    except:
        return render_template("index.html")


movie_id = []


@app.route("/edit", methods=["POST", "GET"])
def edit():
    form = EditFrom()
    movie_id.append(request.args.get("movie_id"))
    print(movie_id)
    return render_template("/edit.html",
                           form=form
                           )


@app.route("/edit_form", methods=["POST", "GET"])
def edit_form():
    with app.app_context():
        movie_data = db.session.execute(db.select(Movie10).filter_by(id=int(movie_id[0]))).scalar()
        new_rating = request.form.get("new_rating")
        new_review = request.form.get("new_review")
        movie_data.rating = new_rating
        movie_data.review = new_review
        db.session.commit()
        movie_id.clear()
        return redirect("/")


@app.route("/delete", methods=["POST", "GET"])
def delete():
    with app.app_context():
        movie_id = request.args.get("movie_id")
        to_delete = db.session.execute(db.select(Movie10).filter_by(id=movie_id)).scalar()
        db.session.delete(to_delete)
        db.session.commit()
        return redirect("/")


# Consult TMBD API for the movie title provided by user and adds the relevant data to db
@app.route("/add", methods=["POST", "GET"])
def add():
    form = EditFrom()
    if request.method == "POST":
        new_movie = request.form.get("new_movie")
        url = "https://api.themoviedb.org/3/search/movie"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer TOKEN HERE"
        }
        params = {
            "query": new_movie
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return render_template("/select.html",
                               results=response.json())
    return render_template("/add.html",
                           form=form)


@app.route("/select", methods=["POST", "GET"])
def select():
    name = request.args.get("movie_name")
    year = request.args.get("release_date").split("-")[0]
    url = "https://api.themoviedb.org/3/search/movie"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer TOKEN HERE"
    }
    params = {
        "query": name,
        "year": year
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    title = response.json()["results"][0]["original_title"]
    year = response.json()["results"][0]["release_date"].split("-")[0]
    description = response.json()["results"][0]["overview"]
    img_url = "https://www.themoviedb.org/t/p/original" + response.json()["results"][0]["poster_path"]
    with app.app_context():
        new_data = Movie10(title=title,
                           year=year,
                           description=description,
                           img_url=img_url,
                           rating=0,
                           review="",
                           ranking=0)
        db.session.add(new_data)
        db.session.commit()
        return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
