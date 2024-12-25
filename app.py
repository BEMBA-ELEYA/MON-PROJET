from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import os

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'Marketplaceuniversitaire'

mysql = MySQL(app)




@app.route('/')
def index():
    search = request.args.get('search', '')
    type_annonce = request.args.get('type', '')

    query = "SELECT ID_Annonce, Nom, Description, Prix, Date_publication, Type_Annonce FROM Annonce WHERE Nom LIKE %s"
    params = [f'%{search}%']

    if type_annonce:
        query += " AND Type_Annonce = %s"
        params.append(type_annonce)

    cur = mysql.connection.cursor()
    cur.execute(query, tuple(params))
    annonces = cur.fetchall()


    annonce_with_photos = []
    for annonce in annonces:
        cur.execute("SELECT IRL FROM Photo WHERE ID_Annonce = %s", (annonce[0],))
        photo = cur.fetchone()
        annonce_with_photos.append((annonce, photo[0] if photo else None))

    cur.close()
    return render_template('index.html', annonces=annonce_with_photos)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Etudiant WHERE Email = %s AND Mot_de_passe = %s", (email, password))
        etudiant = cur.fetchone()
        cur.close()
        if etudiant:
            return redirect(url_for('dashboard', matricule=etudiant[0]))
        else:
            return "Email ou mot de passe incorrect"
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form['telephone']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Etudiant (Nom, Prenom, Numero_telephone, Email, Mot_de_passe) VALUES (%s, %s, %s, %s, %s)",
            (nom, prenom, telephone, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/dashboard/<int:matricule>', methods=['GET', 'POST'])
def dashboard(matricule):
    if request.method == 'POST':
        nom = request.form['nom']
        description = request.form['description']
        prix = request.form['prix']
        type_annonce = request.form['type_annonce']


        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':

                image_folder = os.path.join('static', 'images')


                if not os.path.exists(image_folder):
                    os.makedirs(image_folder)

                image_filename = f"{image.filename}"
                image_path = os.path.join(image_folder, image_filename)


                image.save(image_path)
            else:
                image_filename = None
        else:
            image_filename = None

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO Annonce (Nom, Description, Prix, Date_publication, Type_Annonce, Matricule) VALUES (%s, %s, %s, CURDATE(), %s, %s)',(nom, description, prix, type_annonce, matricule))
        mysql.connection.commit()


        if image_filename:
            cur.execute("SELECT LAST_INSERT_ID()")
            id_annonce = cur.fetchone()[0]
            cur.execute("INSERT INTO Photo (IRL, ID_Annonce) VALUES (%s, %s)", (f"images/{image_filename}", id_annonce))
            mysql.connection.commit()

        cur.close()
        return redirect(url_for('dashboard', matricule=matricule))

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT ID_Annonce, Nom, Description, Prix, Date_publication, Type_Annonce FROM Annonce WHERE Matricule = %s",
        (matricule,))
    annonces = cur.fetchall()


    annonce_with_photos = []
    for annonce in annonces:
        cur.execute("SELECT IRL FROM Photo WHERE ID_Annonce = %s", (annonce[0],))
        photo = cur.fetchone()
        annonce_with_photos.append((annonce, photo[0] if photo else None))

    cur.close()
    return render_template('dashboard.html', annonces=annonce_with_photos, matricule=matricule)


@app.route('/edit_ad/<id_Annonce>/<matricule>', methods=['GET', 'POST'])
def edit_ad(id_Annonce, matricule):
    try:
        # محاولة تحويل المعلمات إلى أعداد صحيحة
        id_Annonce = int(id_Annonce)
        matricule = int(matricule)
    except ValueError:
        return "Invalid ID or Matricule", 400

    cur = mysql.connection.cursor()

    # التحقق من وجود الإعلان في قاعدة البيانات
    cur.execute("SELECT * FROM Annonce WHERE ID_Annonce = %s", (id_Annonce,))
    annonce = cur.fetchone()
    if not annonce:
        cur.close()
        return "Annonce introuvable", 404

    # التحقق من وجود الطالب في قاعدة البيانات
    cur.execute("SELECT * FROM Etudiant WHERE Matricule = %s", (matricule,))
    etudiant = cur.fetchone()
    if not etudiant:
        cur.close()
        return "Matricule introuvable", 404

    # إذا كانت كل الأمور سليمة، نعرض الصفحة
    if request.method == 'POST':
        # بيانات الإعلان يتم تحديثها هنا
        nom = request.form['nom']
        description = request.form['description']
        prix = request.form['prix']
        type_annonce = request.form['type_annonce']

        # إذا كانت هناك صورة جديدة تم تحميلها
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                image_filename = f"images/{image.filename}"
                image.save(f"static/{image_filename}")
                cur.execute("UPDATE Photo SET IRL = %s WHERE ID_Annonce = %s", (image_filename, id_Annonce))
            else:
                # إذا لم يتم رفع صورة جديدة، لا نقوم بتحديث الصورة
                cur.execute("SELECT IRL FROM Photo WHERE ID_Annonce = %s", (id_Annonce,))
                existing_photo = cur.fetchone()
                if not existing_photo:
                    image_filename = None
                else:
                    image_filename = existing_photo[0]
            mysql.connection.commit()

        # تحديث بيانات الإعلان
        cur.execute("UPDATE Annonce SET Nom = %s, Description = %s, Prix = %s, Type_Annonce = %s WHERE ID_Annonce = %s",
                    (nom, description, prix, type_annonce, id_Annonce))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('dashboard', matricule=matricule))

    cur.close()

    # إذا كانت طريقة الطلب هي GET، نعرض البيانات السابقة للإعلان
    return render_template('edit_ad.html', annonce=annonce, matricule=matricule)

@app.route('/delete_ad/<int:id_Annonce>/<int:matricule>')
def delete_ad(id_Annonce, matricule):
    cur = mysql.connection.cursor()


    cur.execute("SELECT IRL FROM Photo WHERE ID_Annonce = %s", (id_Annonce,))
    photos = cur.fetchall()


    for photo in photos:
        photo_path = os.path.join('static', photo[0])
        if os.path.exists(photo_path):
            os.remove(photo_path)


    cur.execute("DELETE FROM Photo WHERE ID_Annonce = %s", (id_Annonce,))
    mysql.connection.commit()


    cur.execute("DELETE FROM Annonce WHERE ID_Annonce = %s", (id_Annonce,))
    mysql.connection.commit()

    cur.close()
    return redirect(url_for('dashboard', matricule=matricule))


if __name__ == '__main__':
    app.run(debug=True)