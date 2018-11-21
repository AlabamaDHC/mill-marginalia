from app import db
from sqlalchemy.ext.hybrid import hybrid_property


class Page(db.Model):
    id = db.Column('page_id', db.Integer, primary_key=True)
    page_num = db.Column(db.String(150))
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'))

    location_in_book = db.Column(db.String(150))

    page_image = db.Column(db.String(150))
    page_order = db.Column(db.Integer)

    marginalia = db.relationship('Marginalia', backref='page', lazy='dynamic')

    @hybrid_property
    def marginalia_type_set(self):
        m = set()
        if self.marginalia:
            for marg in self.marginalia:
                m.add(marg.type)
        return m

    @hybrid_property
    def marginalia_transcription(self):
        transcription = ""
        if self.marginalia:
            for marg in self.marginalia:
                transcription = transcription + " " + marg.transcription
        return transcription


    def __init__(self, page_num, book_id, location_in_book, page_image, page_order):
        self.page_num = page_num
        self.book_id = book_id
        self.location_in_book = location_in_book
        self.page_image = page_image
        self.page_order = page_order


    def serialize(self, includeRelations=False, forAJAX=False, includePrivate=False, imageRoot='assets/pages/', imageExt='.jpg'):
        json = {
            'page_id': self.id,
            'page_num': self.page_num,
            # 'location_in_book': self.location_in_book,
            # 'part_of_book': self.part_of_book,
            # 'page_image': url_for('static', filename=imageRoot+self.page_image+imageExt),
            'page_image': self.page_image,
            # 'page_order': self.page_order,
            'marginalia_type_set': list(self.marginalia_type_set)
        }

        m = list()
        for marg in self.marginalia:
            m.append(marg.serialize())
        json['marginalia'] = m
        if forAJAX:
            return json

        if includeRelations:
            json['book_id'] = self.book_id

        return json

