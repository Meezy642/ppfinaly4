from sqlalchemy.ext.hybrid import hybrid_property
from models import db
from models.category import Category

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)
    Cost = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    Price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    Stock = db.Column(db.Integer, nullable=True, default=0)
    CategoryId = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    images = db.relationship('ProductImage', backref='product_rel', lazy=True, cascade='all, delete-orphan')

    # Hybrid properties for seamless SQL query and Python instance compatibility
    @hybrid_property
    def title(self):
        return self.name

    @title.setter
    def title(self, val):
        self.name = val

    @title.expression
    def title(cls):
        return cls.name

    @hybrid_property
    def price(self):
        return float(self.Price) if self.Price is not None else 0.0

    @price.setter
    def price(self, val):
        self.Price = val

    @price.expression
    def price(cls):
        return cls.Price

    @hybrid_property
    def cost(self):
        return float(self.Cost) if self.Cost is not None else 0.0

    @cost.setter
    def cost(self, val):
        self.Cost = val

    @cost.expression
    def cost(cls):
        return cls.Cost

    @hybrid_property
    def stock(self):
        return self.Stock if self.Stock is not None else 0

    @stock.setter
    def stock(self, val):
        self.Stock = val

    @stock.expression
    def stock(cls):
        return cls.Stock

    @hybrid_property
    def image(self):
        return self.thumbnail or ''

    @image.setter
    def image(self, val):
        self.thumbnail = val

    @image.expression
    def image(cls):
        return cls.thumbnail

    @hybrid_property
    def category_id(self):
        return self.CategoryId

    @category_id.setter
    def category_id(self, val):
        self.CategoryId = val

    @category_id.expression
    def category_id(cls):
        return cls.CategoryId

    @hybrid_property
    def category(self):
        if self.category_rel:
            return self.category_rel.name
        return "general"

    @category.expression
    def category(cls):
        return db.select(Category.name).where(Category.id == cls.CategoryId).scalar_subquery()

    @hybrid_property
    def rating_rate(self):
        return 4.5

    @rating_rate.expression
    def rating_rate(cls):
        return 4.5

    @hybrid_property
    def rating_count(self):
        return 10

    @rating_count.expression
    def rating_count(cls):
        return 10

    def to_dict(self):
        img = self.thumbnail or ''
        if img and not img.startswith('http://') and not img.startswith('https://') and not img.startswith('/') and not img.startswith('data:'):
            img = f"/static/uploads/{img}"

        rate_val = 4.5
        count_val = 10
        try:
            from items import items
            for itm in items:
                if itm['id'] == self.id:
                    rate_val = itm.get('rating', {}).get('rate', 4.5)
                    count_val = itm.get('rating', {}).get('count', 10)
                    break
        except Exception:
            pass

        return {
            "id": self.id,
            "name": self.name,
            "title": self.name,
            "thumbnail": img,
            "image": img,
            "Cost": float(self.Cost) if self.Cost is not None else 0.0,
            "cost": float(self.Cost) if self.Cost is not None else 0.0,
            "Price": float(self.Price) if self.Price is not None else 0.0,
            "price": float(self.Price) if self.Price is not None else 0.0,
            "Stock": self.Stock if self.Stock is not None else 0,
            "stock": self.Stock if self.Stock is not None else 0,
            "CategoryId": self.CategoryId,
            "category_id": self.CategoryId,
            "category": self.category,
            "description": self.description or '',
            "rating": {
                "rate": rate_val,
                "count": count_val
            },
            "images": [im.to_dict() for im in self.images] if self.images else []
        }
