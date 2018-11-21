from app import db
from sqlalchemy.ext.hybrid import hybrid_property


class Author(db.Model):
    id = db.Column('author_id', db.Integer, primary_key=True)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    image = db.Column(db.String(150))
    image_caption = db.Column(db.String(300))
    books = db.relationship('Book', backref='author', lazy='dynamic')
    public = db.Column(db.Boolean, default=True)

    def __init__(self, first_name, last_name, image, image_caption):
        self.first_name = first_name
        self.last_name = last_name
        self.image = image
        self.image_caption = image_caption


    def __init__(self, author):
        self.id = author.id
        self.first_name = author.first_name
        self.last_name = author.last_name
        self.image = author.image
        self.image_caption = author.image_caption
        self.books = author.books
        self.public = author.public


    @hybrid_property
    def titles(self):
        titles = set()
        if self.books:
            for book in self.books:
                titles.add(book.title)
        return titles

    @hybrid_property
    def spine_slugs(self):
        spine_slugs = set()
        if self.books:
            for book in self.books:
                spine_slugs.add(book.spine_image[:-4])
        return spine_slugs
