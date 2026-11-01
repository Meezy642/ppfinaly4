from models import db

class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProductId = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    @property
    def product_id(self):
        return self.ProductId

    @product_id.setter
    def product_id(self, val):
        self.ProductId = val

    def to_dict(self):
        img_name = self.name or ''
        if img_name.startswith(('http://', 'https://', '/')):
            url = img_name
        else:
            url = f"/static/uploads/{img_name}"
        return {
            'id': self.id,
            'ProductId': self.ProductId,
            'product_id': self.ProductId,
            'name': self.name,
            'image_url': url
        }
