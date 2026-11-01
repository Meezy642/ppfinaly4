import json
import urllib.parse
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response
from extensions import db
from models.product import Product
from models.category import Category
from models.order import Order
from models.contact import Contact
from models.user import User
from items import items
from . import front_bp

@front_bp.route("/")
def home():
    prods = Product.query.order_by(Product.id.asc()).all()
    if prods:
        product_list = [p.to_dict() for p in prods]
    else:
        product_list = items
    return render_template("customer/index.html", item=product_list, products=product_list)

@front_bp.route("/products")
def products():
    category = request.args.get("category")
    search_query = request.args.get("search", "").strip()

    query = Product.query
    if category and category != "all":
        query = query.filter_by(category=category)
    if search_query:
        query = query.filter(Product.title.ilike(f"%{search_query}%"))

    prods = query.all()
    if prods:
        product_list = [p.to_dict() for p in prods]
    else:
        product_list = items
        if category and category != "all":
            product_list = [p for p in product_list if p.get("category") == category]
        if search_query:
            product_list = [p for p in product_list if search_query.lower() in p.get("title", "").lower()]

    categories = [c.name for c in Category.query.all()]
    if not categories:
        categories = list(set([p.get("category", "") for p in items]))
    return render_template("customer/products.html", item=product_list, products=product_list, categories=categories, current_category=category)

@front_bp.route("/product/<int:item_id>")
def product_detail(item_id):
    product = Product.query.get(item_id)
    if not product:
        product = next((p for p in items if p.get("id") == item_id), None)
    prod_dict = product.to_dict() if hasattr(product, 'to_dict') else product

    from customer.routes import get_wishlist_from_cookie
    wishlist = get_wishlist_from_cookie()
    in_wishlist = item_id in wishlist

    gallery_images = []
    if isinstance(prod_dict, dict) and prod_dict.get('images'):
        for img_obj in prod_dict['images']:
            url = img_obj.get('image_url') or img_obj.get('name')
            if url and url not in gallery_images:
                gallery_images.append(url)
    if not gallery_images:
        gallery_images = [
            f'/static/uploads/fakestore/product_{item_id}.jpg',
            f'/static/uploads/gallery/product_{item_id}_angle_2.jpg',
            f'/static/uploads/gallery/product_{item_id}_angle_3.jpg',
            f'/static/uploads/gallery/product_{item_id}_angle_4.jpg'
        ]
    fallback_angles = [
        f'/static/uploads/fakestore/product_{item_id}.jpg',
        f'/static/uploads/gallery/product_{item_id}_angle_2.jpg',
        f'/static/uploads/gallery/product_{item_id}_angle_3.jpg',
        f'/static/uploads/gallery/product_{item_id}_angle_4.jpg'
    ]
    for fb in fallback_angles:
        if len(gallery_images) >= 4:
            break
        if fb not in gallery_images:
            gallery_images.append(fb)
    while len(gallery_images) < 4:
        gallery_images.append(gallery_images[0])
    gallery_images = gallery_images[:4]

    return render_template(
        "customer/view_product.html",
        item=prod_dict,
        product=prod_dict,
        in_wishlist=in_wishlist,
        wishlist=wishlist,
        gallery_images=gallery_images,
        gallery=gallery_images
    )

@front_bp.route("/favorites")
@front_bp.route("/wishlist")
def favorites():
    from customer.routes import favorites as customer_favorites
    return customer_favorites()

@front_bp.route('/add_to_wishlist/<int:item_id>', methods=['GET', 'POST'])
@front_bp.route('/add-to-wishlist/<int:item_id>', methods=['GET', 'POST'])
def add_to_wishlist(item_id):
    from customer.routes import add_to_wishlist as customer_add_wish
    return customer_add_wish(item_id)

@front_bp.route('/remove_from_wishlist/<int:item_id>', methods=['GET', 'POST'])
@front_bp.route('/remove-from-wishlist/<int:item_id>', methods=['GET', 'POST'])
def remove_from_wishlist(item_id):
    from customer.routes import remove_from_wishlist as customer_rem_wish
    return customer_rem_wish(item_id)

@front_bp.route("/cart")
def cart():
    from customer.routes import get_cart_from_cookie
    cart_data = get_cart_from_cookie()
    cart_items = []
    total_price = 0.0

    for item_id_str, qty in cart_data.items():
        try:
            item_id = int(item_id_str)
            prod = Product.query.get(item_id)
            if prod:
                prod_dict = prod.to_dict()
            else:
                prod_dict = next((p for p in items if p.get("id") == item_id), None)
            
            if prod_dict:
                price = float(prod_dict.get("price", 0.0))
                subtotal = price * int(qty)
                total_price += subtotal
                cart_items.append({
                    "product": prod_dict,
                    "quantity": int(qty),
                    "item_total": subtotal,
                    "subtotal": subtotal,
                    "total": subtotal
                })
        except Exception:
            continue

    return render_template("customer/cart.html", cart_items=cart_items, total=total_price, total_price=total_price)

@front_bp.route('/add_to_cart/<int:item_id>', methods=['GET', 'POST'])
@front_bp.route('/add-to-cart/<int:item_id>', methods=['GET', 'POST'])
def add_to_cart(item_id):
    from customer.routes import add_to_cart as customer_add_to_cart
    return customer_add_to_cart(item_id)

@front_bp.route('/increase_cart/<int:item_id>', methods=['GET', 'POST'])
@front_bp.route('/increase-cart/<int:item_id>', methods=['GET', 'POST'])
def increase_cart(item_id):
    from customer.routes import increase_cart as customer_inc_cart
    return customer_inc_cart(item_id)

@front_bp.route('/decrease_cart/<int:item_id>', methods=['GET', 'POST'])
@front_bp.route('/decrease-cart/<int:item_id>', methods=['GET', 'POST'])
def decrease_cart(item_id):
    from customer.routes import decrease_cart as customer_dec_cart
    return customer_dec_cart(item_id)

@front_bp.route('/remove_from_cart/<int:item_id>', methods=['GET', 'POST'])
@front_bp.route('/remove-from-cart/<int:item_id>', methods=['GET', 'POST'])
def remove_from_cart(item_id):
    from customer.routes import remove_from_cart as customer_rem_cart
    return customer_rem_cart(item_id)

@front_bp.route('/clear_cart', methods=['GET', 'POST'])
@front_bp.route('/clear-cart', methods=['GET', 'POST'])
def clear_cart():
    from customer.routes import clear_cart as customer_clr_cart
    return customer_clr_cart()

@front_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    from customer.routes import checkout as customer_checkout, place_order as customer_place_order
    if request.method == "POST":
        return customer_place_order()
    return customer_checkout()

@front_bp.route("/place_order", methods=["POST"])
def place_order():
    from customer.routes import place_order as customer_place_order
    return customer_place_order()

@front_bp.route("/order_success")
def order_success():
    from customer.routes import order_success as customer_order_success
    return customer_order_success()

@front_bp.route("/contact", methods=["GET", "POST"])
def contact():
    from customer.routes import contact as customer_contact
    return customer_contact()
