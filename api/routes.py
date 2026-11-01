import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models.category import Category
from models.product import Product
from models.product_image import ProductImage
from models.user import User

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ==========================================
# AUTH API ENDPOINTS
# ==========================================
@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form
    identity = (data.get('username') or data.get('email') or data.get('identity') or '').strip()
    password = data.get('password', '')

    if not identity or not password:
        return jsonify({'success': False, 'message': 'Username/email and password required'}), 400

    user = User.query.filter((User.username == identity) | (User.email == identity)).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['user_email'] = user.email
        session['user_role'] = user.role
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    # Fallback superadmin check
    if identity in ['admin', 'admin@store.com'] and password in ['admin', 'admin123']:
        session['user_id'] = 9999
        session['username'] = 'admin'
        session['user_email'] = 'admin@store.com'
        session['user_role'] = 'Super Administrator'
        return jsonify({
            'success': True,
            'message': 'Login successful (Super Administrator)',
            'user': {
                'id': 9999,
                'username': 'admin',
                'email': 'admin@store.com',
                'role': 'Super Administrator',
                'name': 'Administrator'
            }
        }), 200

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    name = (data.get('name') or username).strip()
    phone_number = (data.get('phone_number') or '').strip()

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email and password required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    user = User(
        username=username,
        email=email,
        name=name,
        phone_number=phone_number,
        role='customer',
        profile_image='no-profile.png'
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': user.to_dict()
    }), 201


@api_bp.route('/auth/me', methods=['GET'])
def api_me():
    username = session.get('username')
    if not username:
        return jsonify({'authenticated': False, 'user': None}), 200
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'authenticated': True, 'user': user.to_dict()}), 200
    return jsonify({
        'authenticated': True,
        'user': {
            'username': username,
            'role': session.get('user_role', 'admin')
        }
    }), 200


@api_bp.route('/auth/logout', methods=['POST', 'GET'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


# ==========================================
# CATEGORY CRUD API (5pts)
# ==========================================
@api_bp.route('/categories', methods=['GET'])
def api_get_categories():
    categories = Category.query.order_by(Category.id.asc()).all()
    return jsonify({
        'success': True,
        'count': len(categories),
        'categories': [c.to_dict() for c in categories]
    }), 200


@api_bp.route('/categories/<int:category_id>', methods=['GET'])
def api_get_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    data = category.to_dict()
    data['products'] = [p.to_dict() for p in category.products]
    return jsonify({'success': True, 'category': data}), 200


@api_bp.route('/categories', methods=['POST'])
def api_create_category():
    data = request.get_json(silent=True) or request.form
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Category name is required'}), 400

    image = (data.get('image') or '').strip()
    # Check for file upload
    file = request.files.get('image_file') or request.files.get('image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        image = f"/static/uploads/{filename}"

    description = (data.get('description') or '').strip()

    category = Category(name=name, image=image, description=description)
    db.session.add(category)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Category created successfully',
        'category': category.to_dict()
    }), 201


@api_bp.route('/categories/<int:category_id>', methods=['PUT', 'PATCH'])
def api_update_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404

    data = request.get_json(silent=True) or request.form
    if 'name' in data and data['name']:
        category.name = data['name'].strip()
    if 'description' in data:
        category.description = data['description'].strip()
    if 'image' in data:
        category.image = data['image'].strip()

    file = request.files.get('image_file') or request.files.get('image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        category.image = f"/static/uploads/{filename}"

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Category updated successfully',
        'category': category.to_dict()
    }), 200


@api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def api_delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Category deleted successfully'}), 200


# ==========================================
# PRODUCT CRUD API (5pts)
# ==========================================
@api_bp.route('/products', methods=['GET'])
def api_get_products():
    category_id = request.args.get('category_id') or request.args.get('CategoryId')
    search = request.args.get('search', '').strip()

    query = Product.query
    if category_id:
        query = query.filter_by(CategoryId=int(category_id))
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.order_by(Product.id.asc()).all()
    return jsonify({
        'success': True,
        'count': len(products),
        'products': [p.to_dict() for p in products]
    }), 200


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    return jsonify({'success': True, 'product': product.to_dict()}), 200


@api_bp.route('/products', methods=['POST'])
def api_create_product():
    data = request.get_json(silent=True) or request.form
    name = (data.get('name') or data.get('title') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Product name is required'}), 400

    price = float(data.get('Price') or data.get('price') or 0.0)
    cost = float(data.get('Cost') or data.get('cost') or 0.0)
    stock = int(data.get('Stock') or data.get('stock') or 0)
    category_id = data.get('CategoryId') or data.get('category_id')
    description = (data.get('description') or '').strip()
    thumbnail = (data.get('thumbnail') or data.get('image') or '').strip()

    if not category_id:
        # Default to first category if available
        first_cat = Category.query.first()
        category_id = first_cat.id if first_cat else 1
    else:
        category_id = int(category_id)

    # Check for file upload
    file = request.files.get('thumbnail_file') or request.files.get('image_file') or request.files.get('thumbnail')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        thumbnail = f"/static/uploads/{filename}"

    product = Product(
        name=name,
        thumbnail=thumbnail,
        Cost=cost,
        Price=price,
        Stock=stock,
        CategoryId=category_id,
        description=description
    )
    db.session.add(product)
    db.session.commit()

    # Automatically add initial ProductImage if thumbnail provided
    if thumbnail:
        img = ProductImage(ProductId=product.id, name=thumbnail)
        db.session.add(img)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Product created successfully',
        'product': product.to_dict()
    }), 201


@api_bp.route('/products/<int:product_id>', methods=['PUT', 'PATCH'])
def api_update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    data = request.get_json(silent=True) or request.form
    if 'name' in data and data['name']:
        product.name = data['name'].strip()
    elif 'title' in data and data['title']:
        product.name = data['title'].strip()

    if 'Price' in data or 'price' in data:
        product.Price = float(data.get('Price') or data.get('price') or 0.0)
    if 'Cost' in data or 'cost' in data:
        product.Cost = float(data.get('Cost') or data.get('cost') or 0.0)
    if 'Stock' in data or 'stock' in data:
        product.Stock = int(data.get('Stock') or data.get('stock') or 0)
    if 'CategoryId' in data or 'category_id' in data:
        product.CategoryId = int(data.get('CategoryId') or data.get('category_id'))
    if 'description' in data:
        product.description = data['description'].strip()
    if 'thumbnail' in data or 'image' in data:
        product.thumbnail = (data.get('thumbnail') or data.get('image') or '').strip()

    file = request.files.get('thumbnail_file') or request.files.get('image_file') or request.files.get('thumbnail')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        product.thumbnail = f"/static/uploads/{filename}"

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Product updated successfully',
        'product': product.to_dict()
    }), 200


@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product deleted successfully'}), 200


# ==========================================
# PRODUCT IMAGE CRUD API (5pts)
# ==========================================
@api_bp.route('/products/<int:product_id>/images', methods=['GET'])
def api_get_product_images(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    images = ProductImage.query.filter_by(ProductId=product_id).all()
    return jsonify({
        'success': True,
        'count': len(images),
        'images': [img.to_dict() for img in images]
    }), 200


@api_bp.route('/products/<int:product_id>/images', methods=['POST'])
def api_add_product_image(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    data = request.get_json(silent=True) or request.form
    image_name = (data.get('name') or data.get('image') or '').strip()

    file = request.files.get('image') or request.files.get('file')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        image_name = filename

    if not image_name:
        return jsonify({'success': False, 'message': 'Image name or file is required'}), 400

    new_img = ProductImage(ProductId=product_id, name=image_name)
    db.session.add(new_img)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Product image added successfully',
        'image': new_img.to_dict()
    }), 201


@api_bp.route('/product-images/<int:image_id>', methods=['DELETE'])
def api_delete_product_image(image_id):
    img = ProductImage.query.get(image_id)
    if not img:
        return jsonify({'success': False, 'message': 'Product image not found'}), 404

    db.session.delete(img)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product image deleted successfully'}), 200


# ==========================================
# USER CRUD API (upload image)
# ==========================================
@api_bp.route('/users', methods=['GET'])
def api_get_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify({
        'success': True,
        'count': len(users),
        'users': [u.to_dict() for u in users]
    }), 200


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({'success': True, 'user': user.to_dict()}), 200


@api_bp.route('/users', methods=['POST'])
def api_create_user():
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password', '123456')
    name = (data.get('name') or username).strip()
    phone_number = (data.get('phone_number') or '').strip()
    role = (data.get('role') or 'customer').strip().lower()

    if not username or not email:
        return jsonify({'success': False, 'message': 'Username and email are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    profile_image = 'no-profile.png'
    file = request.files.get('profile') or request.files.get('image') or request.files.get('profile_image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        profile_image = filename

    user = User(
        username=username,
        email=email,
        name=name,
        phone_number=phone_number,
        role=role,
        profile_image=profile_image
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@api_bp.route('/users/<int:user_id>', methods=['PUT', 'PATCH'])
def api_update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    data = request.get_json(silent=True) or request.form
    if 'username' in data and data['username']:
        new_username = data['username'].strip()
        if new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return jsonify({'success': False, 'message': 'Username already taken'}), 409
            user.username = new_username

    if 'email' in data and data['email']:
        new_email = data['email'].strip()
        if new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                return jsonify({'success': False, 'message': 'Email already taken'}), 409
            user.email = new_email

    if 'name' in data:
        user.name = data['name'].strip()
    if 'phone_number' in data:
        user.phone_number = data['phone_number'].strip()
    if 'role' in data:
        user.role = data['role'].strip().lower()
    if 'password' in data and data['password']:
        user.set_password(data['password'])

    file = request.files.get('profile') or request.files.get('image') or request.files.get('profile_image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        user.profile_image = filename

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
