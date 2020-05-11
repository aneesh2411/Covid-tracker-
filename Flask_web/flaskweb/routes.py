import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from flaskweb import app, db, bcrypt
from flaskweb.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskweb.models import User
from flask_login import login_user, current_user, logout_user, login_required
from flask import Flask,render_template,redirect,request,url_for,session
import requests
from bs4 import BeautifulSoup

def dataRetriever():

    class Country:
        def __init__(self,countryName,totalCases,activeCases,totalDeath,totalCured,casesToday):
            self.countryName = countryName
            self.totalCases = totalCases
            self.activeCases = activeCases
            self.totalDeath = totalDeath
            self.totalCured = totalCured
            self.casesToday = casesToday

    page = requests.get('https://www.worldometers.info/coronavirus/')
    soup = BeautifulSoup(page.content,'html.parser')
    table = soup.find(id='main_table_countries_today').find('tbody').find_all('tr')

    l = []
    for i in table:
        all_td = i.find_all('td')
        countryName = all_td[0].get_text()
        totalCases = all_td[1].get_text()
        activeCases = all_td[6].get_text()
        totalDeath = all_td[3].get_text()
        totalCured = all_td[5].get_text()
        casesToday = all_td[2].get_text()

        countryName = Country(countryName,totalCases,activeCases,totalDeath,totalCured,casesToday)
        l.append(countryName)
    return l    

countrylist = dataRetriever()

def getCountry(countryName):
    listOfall = countrylist
    for i in listOfall:
        if i.countryName==countryName:
            return i


@app.route("/",methods=['GET','POST'])
@app.route("/home",methods=['GET','POST'])
def home():
    if request.method=='POST':
        countryName = request.form['action']
        a = getCountry(countryName)
    else:
        a=getCountry('World')
    return render_template('home.html',data = countrylist,country = a)


@app.route("/symptoms")
def symptoms():
    return render_template('symptoms.html', title='symptoms')

@app.route("/prevention")
def prevention():
    return render_template('prevention.html', title='prevention')
	
@app.route("/treatment")
def treatment():
    return render_template('treatment.html', title='treatment')	

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

	


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)