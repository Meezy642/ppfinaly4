from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.category import Category
from models.product_image import ProductImage
from models.product import Product
from models.user import User
from models.order import Order
from models.contact import Contact

__all__ = ['db', 'Category', 'Product', 'ProductImage', 'User', 'Order', 'Contact']
