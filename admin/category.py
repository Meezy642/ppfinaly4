import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Category, Product
from admin.dashboard import admin_required

category_bp = Blueprint('admin_category', __name__, url_prefix='/admin')

@category_bp.route('/categories')
@admin_required
def admin_categories():
    categories = Category.query.order_by(Category.id.asc()).all()
    total_products = Product.query.count()
    return render_template('admin/categories.html', categories=categories, total_products=total_products)

@category_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image', '').strip()

        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for('admin_category.admin_add_category'))

        # Check for image upload
        uploaded_file = request.files.get('image_file') or request.files.get('image')
        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
            os.makedirs(upload_folder, exist_ok=True)
            uploaded_file.save(os.path.join(upload_folder, filename))
            final_image = f"/static/uploads/{filename}"
        else:
            final_image = image_url

        new_cat = Category(
            name=name,
            image=final_image,
            description=description
        )
        db.session.add(new_cat)
        db.session.commit()

        flash(f"Category '{name}' created successfully!", "success")
        return redirect(url_for('admin_category.admin_categories'))

    return render_template('admin/category_form.html', edit_mode=False)

@category_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin_category.admin_categories'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image', '').strip()

        if not name:
            flash("Category name cannot be empty.", "danger")
            return render_template('admin/category_form.html', edit_mode=True, category=category)

        category.name = name
        category.description = description

        uploaded_file = request.files.get('image_file') or request.files.get('image')
        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
            os.makedirs(upload_folder, exist_ok=True)
            uploaded_file.save(os.path.join(upload_folder, filename))
            category.image = f"/static/uploads/{filename}"
        elif image_url:
            category.image = image_url

        db.session.commit()
        flash(f"Category '{category.name}' updated successfully!", "success")
        return redirect(url_for('admin_category.admin_categories'))

    return render_template('admin/category_form.html', edit_mode=True, category=category)

@category_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin_category.admin_categories'))

    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f"Category '{name}' deleted successfully!", "success")
    return redirect(url_for('admin_category.admin_categories'))
