import os
from flask import current_app, flash, redirect, render_template, request, url_for, session
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from . import admin_bp

def admin_only_check():
    role = session.get('user_role')
    username = session.get('username')
    if role in ['Super Administrator', 'admin']:
        return None
    if username:
        user = User.query.filter_by(username=username).first()
        if user and user.role == 'staff':
            flash("Access denied: Staff members cannot access the User Management portal.", "danger")
            return redirect(url_for('admin_dashboard.admin_dashboard'))
    return None

# </admin/user>
@admin_bp.route("/user")
@admin_bp.route("/users")
def user_index():
    denied = admin_only_check()
    if denied:
        return denied

    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin/user/index.html", users=users)

# </admin/user/create>
@admin_bp.route("/user/create", methods=["GET", "POST"])
@admin_bp.route("/users/add", methods=["GET", "POST"])
def user_create():
    denied = admin_only_check()
    if denied:
        return denied

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        phone_number = request.form.get("phone_number", "").strip()
        role = request.form.get("role", "customer").lower()
        name = request.form.get("name", username).strip()

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("admin/user/create.html", edit_mode=False)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists! Please use a different email.", "danger")
            return render_template("admin/user/create.html", edit_mode=False)

        if User.query.filter_by(username=username).first():
            flash("Username already exists! Please choose a different username.", "danger")
            return render_template("admin/user/create.html", edit_mode=False)

        if phone_number and User.query.filter_by(phone_number=phone_number).first():
            flash(f"Phone number '{phone_number}' is already registered! Please use a different phone number.", "danger")
            return render_template("admin/user/create.html", edit_mode=False)

        # File upload for profile image
        file = request.files.get("profile") or request.files.get("image") or request.files.get("profile_image")
        profile_path = "no-profile.png"

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            upload_folder = current_app.config.get("UPLOAD_FOLDER", os.path.join(current_app.root_path, "static", "uploads"))
            os.makedirs(upload_folder, exist_ok=True)
            file_save_path = os.path.join(upload_folder, filename)
            file.save(file_save_path)
            profile_path = filename

        # save to db
        new_user = User(
            username=username,
            email=email,
            profile_image=profile_path,
            phone_number=phone_number,
            role=role,
            name=name
        )
        new_user.set_password(password or '123456')

        db.session.add(new_user)
        db.session.commit()

        flash("User created successfully!", "success")
        return redirect(url_for("admin.user_index"))

    return render_template("admin/user/create.html", edit_mode=False)

# </admin/user/edit/<id>>
@admin_bp.route("/user/edit/<int:id>", methods=["GET", "POST"])
@admin_bp.route("/users/edit/<int:id>", methods=["GET", "POST"])
def user_edit(id):
    denied = admin_only_check()
    if denied:
        return denied

    user = User.query.get(id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.user_index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        role = request.form.get("role", "customer").lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        if email and email != user.email:
            existing_user = User.query.filter(User.email == email, User.id != user.id).first()
            if existing_user:
                flash("Email already exists! Please use a different email.", "danger")
                return render_template("admin/user/edit.html", user=user, edit_mode=True, edit_username=user.username)
            user.email = email

        if username and username != user.username:
            if User.query.filter(User.username == username, User.id != user.id).first():
                flash("Username already exists! Please choose a different username.", "danger")
                return render_template("admin/user/edit.html", user=user, edit_mode=True, edit_username=user.username)
            user.username = username

        if phone_number:
            existing_phone = User.query.filter(User.phone_number == phone_number, User.id != user.id).first()
            if existing_phone:
                flash(f"Phone number '{phone_number}' is already registered! Please use a different phone number.", "danger")
                return render_template("admin/user/edit.html", user=user, edit_mode=True, edit_username=user.username)
            user.phone_number = phone_number
        elif phone_number == '':
            user.phone_number = ''

        if role:
            user.role = role
        if name:
            user.name = name
        if password:
            user.set_password(password)

        file = request.files.get("profile") or request.files.get("image") or request.files.get("profile_image")
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            upload_folder = current_app.config.get("UPLOAD_FOLDER", os.path.join(current_app.root_path, "static", "uploads"))
            os.makedirs(upload_folder, exist_ok=True)
            file_save_path = os.path.join(upload_folder, filename)
            file.save(file_save_path)
            user.profile_image = filename

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin.user_index"))

    return render_template("admin/user/edit.html", user=user, edit_mode=True, edit_username=user.username, user_data=user.to_dict())

# </admin/user/delete/<id>>
@admin_bp.route("/user/delete/<int:id>", methods=["GET", "POST"])
@admin_bp.route("/users/delete/<int:id>", methods=["GET", "POST"])
def user_delete(id):
    denied = admin_only_check()
    if denied:
        return denied

    user = User.query.get(id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.user_index"))

    if session.get("username") == user.username:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.user_index"))

    if request.method == "POST":
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
        return redirect(url_for("admin.user_index"))

    return render_template("admin/user/delete.html", user=user)

# User Details
@admin_bp.route('/users/<int:id>')
@admin_bp.route('/user/<int:id>')
def user_details(id):
    user = User.query.get(id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.user_index'))
    return render_template('admin/user_detail.html', user=user)
