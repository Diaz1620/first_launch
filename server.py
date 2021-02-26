from flask import Flask, render_template,request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
app = Flask(__name__)
app.secret_key = "keychain"
bcrypt = Bcrypt(app)

import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 
name = re.compile(r'^[a-zA-Z]{2,50}$')
password = re.compile(r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,20}$')


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def register():
    mysql2 = connectToMySQL('recipes')
    query2 = "SELECT email FROM users WHERE email = %(user)s;"

    is_valid = True
    if not name.match(request.form['first']):
        is_valid = False
        flash("First Name Not A Valid Entry!")
        print(request.form['first'])
    if not name.match(request.form['last']):
        is_valid = False
        flash("Last Name Not A Valid Entry!")
        print(request.form['last'])
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Email Not A Valid Entry!")
        print(request.form['email'])
    for email in query2:
        if email == request.form['email']:
            is_valid = False
            flash("Email Is Already In Use")
            print(email)
    if not password.match(request.form['pass']):
        is_valid = False
        flash("Password Not A Valid Entry!")
    if request.form['confirm'] != request.form['pass']:
        is_valid = False
        flash("Passwords Must Match!")
    data2 = {
        "user": request.form["email"]
    }
    result2 = mysql2.query_db(query2,data2)
    if len(result2) > 0:
        is_valid = False
        flash("Email already in use!")
    
    if not is_valid:
        return redirect('/')
    else:
        pw_hash = bcrypt.generate_password_hash(request.form['pass'])  
        print(pw_hash)
        confirm_hash = bcrypt.generate_password_hash(request.form['confirm'])
        mysql = connectToMySQL('recipes')
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(pass_hash)s, Now(), Now());"
        data = {
            "fn": request.form['first'],
            "ln": request.form['last'],
            "em": request.form['email'],
            "pass_hash": pw_hash
        }
        user_id = mysql.query_db(query,data)
        # save the id in session
        session['user_id'] = user_id
        flash("Registered Successfully, Please Login To Continue")
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    mysql = connectToMySQL('recipes')
    query = "SELECT * FROM users where email = %(email)s;"
    data = {
        "email": request.form["loginemail"]
    }
    result = mysql.query_db(query,data)
    if len(result) > 0:
        if bcrypt.check_password_hash(result[0]['password'], request.form['loginpass']):
            session['userid'] = result[0]['id']
            flash("Login Successful")
            return redirect('/success')
        else:
            flash("Email/Username Combination Incorrect!")
            return redirect('/')

@app.route('/success')
def success():
    if "userid" not in session:
        flash('Must Be Logged In To Access Content')
        return redirect('/')
    print(session['userid'])
    # get the logged in user
    mysql = connectToMySQL('recipes')
    query = "SELECT * FROM users where id = %(id)s;"
    data = {
        "id": session['userid']
    }
    name = mysql.query_db(query,data)
    # get recipe info
    mysql = connectToMySQL('recipes')
    query = "SELECT * FROM recipes.users JOIN recipes ON users.id = user_id WHERE users.id = %(id)s;"
    data = {
        "id": session['userid']
    }
    recipe_info = mysql.query_db(query,data)
    return render_template('dashboard.html', user_name = name, recipes = recipe_info)

@app.route('/view_instructions/<recipe_id>')
def view(recipe_id):
    if "userid" not in session:
        flash('Must Be Logged In To Access Content')
        return redirect('/')
    mysql = connectToMySQL('recipes')
    query = "SELECT * FROM recipes WHERE recipes.id = %(recipe_id)s;"
    data = {
        "recipe_id": recipe_id
    }
    recipe_info = mysql.query_db(query,data)
    return render_template('view_instructions.html', recipe = recipe_info)

@app.route('/edit_recipe/<recipe_id>')
def edit(recipe_id):
    mysql = connectToMySQL('recipes')
    query = "SELECT * FROM recipes WHERE recipes.id = %(recipe_id)s;"
    data = {
        "recipe_id": recipe_id
    }
    recipe_info = mysql.query_db(query,data)
    session['recipe_id'] = recipe_id
    return render_template("edit_recipe.html", recipes = recipe_info)

@app.route("/submit_edits", methods=['POST'])
def submit_edit():
    if "userid" not in session:
        flash('Must Be Logged In To Access Content')
    is_valid = True
    if len(request.form['recipe_name']) < 3:
        is_valid = False
        flash("Name Not A Valid Entry!")
        print(request.form['recipe_name'])
    if len(request.form['desc']) < 3:
        is_valid = False
        flash("Desciption Not A Valid Entry!")
        print(request.form['desc'])
    if len(request.form['instructions']) < 3:
        is_valid = False
        flash("Instructions Not A Valid Entry!")
        print(request.form['instructions'])
    # if request.form['time'] != "Yes" or request.form['time'] != "No":
    #     is_valid = False
    #     flash("Selection Must Be Made")
    #     print(request.form['time'])
    if not is_valid:

        flash("All fields are required")
        return redirect(f"/edit_recipe/{session['recipe_id']}")
    else:
        mysql = connectToMySQL('recipes')
        query = "UPDATE recipes.recipes SET name = %(recipe_name)s, description = %(desc)s, instructions = %(inst)s, under_30_min = %(answer)s WHERE recipes.id = %(recipe_id)s;"
        data = {
            "recipe_name": request.form['recipe_name'],
            "desc": request.form['desc'],
            "inst": request.form['instructions'],
            "answer": request.form['time'],
            "recipe_id": session['recipe_id']
        }
        mysql.query_db(query,data)
        return redirect('/success')

@app.route('/create_new_recipe')
def add():
    return render_template("add_recipe.html")

@app.route('/create_recipe', methods=['POST'])
def create():
    if "userid" not in session:
        flash('Must Be Logged In To Access Content')
        return redirect('/')
    is_valid = True
    if len(request.form['recipe_name']) < 3:
        is_valid = False
        flash("Name Not A Valid Entry!")
        print(request.form['recipe_name'])
    if len(request.form['desc']) < 3:
        is_valid = False
        flash("Desciption Not A Valid Entry!")
        print(request.form['desc'])
    if len(request.form['instructions']) < 3:
        is_valid = False
        flash("Instructions Not A Valid Entry!")
        print(request.form['instructions'])
    # if request.form['time'] != "Yes" or request.form['time'] != "No":
    #     is_valid = False
    #     flash("Selection Must Be Made")
    #     print(request.form['time'])
    if not is_valid:
        flash("All fields are required")
        return redirect('/create_new_recipe')
    else:
        mysql = connectToMySQL('recipes')
        query = "INSERT INTO recipes.recipes (name, description, instructions, under_30_min, user_id) VALUES(%(recipe_name)s, %(desc)s, %(inst)s, %(answer)s, %(user_id)s);"
        data = {
            "recipe_name": request.form['recipe_name'],
            "desc": request.form['desc'],
            "inst": request.form['instructions'],
            "answer": request.form['time'],
            "user_id": session['userid']
        }
        mysql.query_db(query,data)
        return redirect('/success')

@app.route('/delete_recipe/<recipes_id>')
def delete(recipes_id):
    if "userid" not in session:
        flash('Must Be Logged In To Access Content')
        return redirect('/')
    mysql = connectToMySQL('recipes')
    query = "DELETE FROM `recipes`.`recipes` WHERE recipes.id = %(recipe_id)s;"
    data = {
        "recipe_id": recipes_id
    }
    mysql.query_db(query,data)
    return redirect('/success')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
