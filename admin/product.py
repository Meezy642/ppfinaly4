import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from models import db, Product, Category, ProductImage
from upload_config import save_uploaded_file
from admin.dashboard import admin_required

product_bp = Blueprint('admin_product', __name__, url_prefix='/admin')

@product_bp.route('/products')
@admin_required
def admin_products():
    products = Product.query.order_by(Product.id.asc()).all()
    return render_template('admin/products.html', products=[p.to_dict() for p in products])

@product_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name') or request.form.get('title', '').strip()
        price = float(request.form.get('price') or request.form.get('Price') or 0.0)
        cost = float(request.form.get('cost') or request.form.get('Cost') or 0.0)
        stock = int(request.form.get('stock') or request.form.get('Stock') or 0)
        category_id_val = request.form.get('category_id') or request.form.get('CategoryId')
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image') or request.form.get('thumbnail', '').strip()

        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for('admin_product.admin_add_product'))

        # Resolve CategoryId
        if category_id_val and category_id_val != '__new__':
            try:
                category_id = int(category_id_val)
            except ValueError:
                cat = Category.query.filter_by(name=category_id_val).first()
                category_id = cat.id if cat else (categories[0].id if categories else 1)
        else:
            new_cat_name = request.form.get('new_category', '').strip()
            if new_cat_name:
                new_cat = Category(name=new_cat_name)
                db.session.add(new_cat)
                db.session.commit()
                category_id = new_cat.id
            else:
                category_id = categories[0].id if categories else 1

        # Check for file upload for thumbnail
        uploaded_file = request.files.get('thumbnail_file') or request.files.get('image_file') or request.files.get('image')
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)

        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(os.path.join(upload_folder, filename))
            final_thumbnail = f"/static/uploads/{filename}"
        else:
            final_thumbnail = image_url

        new_product = Product(
            name=name,
            thumbnail=final_thumbnail,
            Cost=cost,
            Price=price,
            Stock=stock,
            CategoryId=category_id,
            description=description
        )
        db.session.add(new_product)
        db.session.commit()

        # Add initial thumbnail as ProductImage
        if final_thumbnail:
            p_img = ProductImage(ProductId=new_product.id, name=final_thumbnail)
            db.session.add(p_img)
            db.session.commit()

        # Check for additional images upload
        additional_images = request.files.getlist('additional_images')
        for add_file in additional_images:
            if add_file and add_file.filename != '':
                fn = secure_filename(add_file.filename)
                add_file.save(os.path.join(upload_folder, fn))
                img_rec = ProductImage(ProductId=new_product.id, name=fn)
                db.session.add(img_rec)
        db.session.commit()

        flash(f"Product '{name}' added successfully!", "success")
        return redirect(url_for('admin_product.admin_products'))

    return render_template('admin/product_form.html',
        edit_mode=False,
        categories=categories
    )

@product_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for('admin_product.admin_products'))

    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == 'POST':
        name = request.form.get('name') or request.form.get('title', '').strip()
        if name:
            product.name = name

        product.Price = float(request.form.get('price') or request.form.get('Price') or 0.0)
        product.Cost = float(request.form.get('cost') or request.form.get('Cost') or 0.0)
        product.Stock = int(request.form.get('stock') or request.form.get('Stock') or 0)
        product.description = request.form.get('description', '').strip()

        cat_val = request.form.get('category_id') or request.form.get('CategoryId') or request.form.get('category')
        if cat_val:
            try:
                product.CategoryId = int(cat_val)
            except ValueError:
                cat = Category.query.filter_by(name=cat_val).first()
                if cat:
                    product.CategoryId = cat.id

        # Thumbnail removal, upload or URL
        if request.form.get('remove_thumbnail') == '1':
            product.thumbnail = ''

        image_url = request.form.get('image') or request.form.get('thumbnail', '').strip()
        uploaded_file = request.files.get('thumbnail_file') or request.files.get('image_file') or request.files.get('image')
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)

        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(os.path.join(upload_folder, filename))
            product.thumbnail = f"/static/uploads/{filename}"
        elif image_url:
            product.thumbnail = image_url

        # Additional images
        additional_images = request.files.getlist('additional_images')
        for add_file in additional_images:
            if add_file and add_file.filename != '':
                fn = secure_filename(add_file.filename)
                add_file.save(os.path.join(upload_folder, fn))
                img_rec = ProductImage(ProductId=product.id, name=fn)
                db.session.add(img_rec)

        db.session.commit()
        flash(f"Product '{product.name}' updated successfully!", "success")
        return redirect(url_for('admin_product.admin_products'))

    return render_template('admin/product_form.html',
        edit_mode=True,
        product=product.to_dict(),
        product_obj=product,
        categories=categories
    )

@product_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for('admin_product.admin_products'))

    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{name}' deleted successfully!", "success")
    return redirect(url_for('admin_product.admin_products'))

@product_bp.route('/product-images/delete/<int:image_id>', methods=['POST'])
@admin_required
def admin_delete_product_image(image_id):
    img = ProductImage.query.get(image_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json
    if not img:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Product image not found.'}), 404
        flash("Product image not found.", "error")
        return redirect(request.referrer or url_for('admin_product.admin_products'))

    product_id = img.ProductId
    db.session.delete(img)
    db.session.commit()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Product image deleted successfully!'}), 200

    flash("Product image deleted.", "success")
    return redirect(url_for('admin_product.admin_edit_product', product_id=product_id))
