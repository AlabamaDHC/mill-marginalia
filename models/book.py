from app import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, column_property
from sqlalchemy import func, select

from models.page import Page
from models.marginalia import Marginalia


class Book(db.Model):
    id = db.Column('book_id', db.Integer, primary_key=True)

    slug = db.Column(db.String(50), unique=True)
    human_slug = db.Column(db.String(50), unique=True)
    title = db.Column(db.String(150))
    subtitle = db.Column(db.String(150))

    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'))
    author_first_name = db.Column(db.String(150)) #TODO: remove these in favor of the author object. Front end views should already be using Author obj
    author_last_name = db.Column(db.String(150))  #TODO: remove these in favor of the author object. Front end views should already be using Author obj
    editor_translator = db.Column(db.String(150))

    edition = db.Column(db.String(150))
    number_of_volumes = db.Column(db.String(150))
    volume_number = db.Column(db.Integer)
    # volume_label = db.Column(db.String(150))
    part_of_book = db.Column(db.String(150))
    # role_in_collection = db.Column(db.String(150))

    publisher = db.Column(db.String(150))
    place_of_pub = db.Column(db.String(150))
    year_of_pub = db.Column(db.String(150))

    spine_image = db.Column(db.String(150))

    full_text_edition_link = db.Column(db.String(300))
    period_translation_link = db.Column(db.String(300))

    public = db.Column(db.Boolean, default=True)
    flag = db.Column(db.Boolean, default=False)
    notes = deferred(db.Column(db.Text))
    raw_import = deferred(db.Column(db.Text))

    critical_intro = db.Column(db.String(150))

    pages = db.relationship('Page', backref='book', lazy='dynamic', order_by="asc(Page.page_order)")
    marginalia = db.relationship('Marginalia', backref='book', lazy='dynamic')

    #add page_count & marginalia_count columns after all of the classes have been define because of import order

    @hybrid_property
    def marginalia_type_set(self):
        m = set()
        if self.pages:
            for page in self.pages:
                if page.marginalia:
                    for marg in page.marginalia:
                        m.add(marg.type)
        return list(m)

    def __init__(self, human_slug, title, subtitle, author_id ,author_first_name, author_last_name, editor_translator, edition,
                 number_of_volumes, volume_number, part_of_book, publisher, place_of_pub, year_of_pub, spine_image, full_text_edition_link,
                 period_translation_link, raw_import):
        self.human_slug = human_slug
        self.slug = human_slug.replace(' ', '-')
        self.title = title
        self.subtitle = subtitle
        self.author_id = author_id
        self.author_first_name = author_first_name
        self.author_last_name = author_last_name
        self.editor_translator = editor_translator
        self.edition = edition
        self.number_of_volumes = number_of_volumes
        self.part_of_book = part_of_book
        self.volume_number = volume_number
        self.publisher = publisher
        self.place_of_pub = place_of_pub
        self.year_of_pub = year_of_pub
        self.spine_image = spine_image
        self.full_text_edition_link = full_text_edition_link
        self.period_translation_link = period_translation_link
        self.raw_import = raw_import

        if part_of_book and part_of_book != "" and part_of_book != " ":
            self.volume_label = part_of_book
            self.flag = True



Book.page_count = column_property(
        select([func.count(Page.id)]).\
            where(Page.book_id==Book.id)
    )

Book.marginalia_count = column_property(
        select([func.count(Marginalia.id)]).\
            where(Marginalia.book_id==Book.id)
    )
