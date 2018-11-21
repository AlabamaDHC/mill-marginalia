import os

import sqlalchemy

from app import db
from sqlalchemy.orm import deferred, column_property

from models.author import Author
from models.book import Book
from models.marginalia import Marginalia
from models.page import Page


col_map = {
        'author_last_name': 0,  # COLUMN A
        'author_first_name': 1,  # COLUMN B
        'title': 2,  # COLUMN C
        'subtitle': 3,  # COLUMN D
        'editor_translator': 4,  # COLUMN E
        'number_of_volumes': 5,  # COLUMN F
        'edition': 6,  # COLUMN G
        'place_of_pub': 7,  # COLUMN H
        'publisher': 8,  # COLUMN I
        'year_of_pub': 9,  # COLUMN J
        'volume_number': 10,  # COLUMN K
        'location_in_book': 11,  # COLUMN L
        'part_of_book': 12,  # COLUMN M
        'page_image': 13,  # COLUMN N
        'close_image': 14,  # COLUMN O
        'page_num': 15,  # COLUMN P
        'location_on_page': 16,  # COLUMN Q
        'line_number': 17,  # COLUMN R
        'writing_implement': 18,  # COLUMN S
        'type': 19,  # COLUMN T
        'subtype': 20,  # COLUMN U
        'language': 21,  # COLUMN V
        'transcription': 22,  # COLUMN W
        'hand': 23,  # COLUMN X
        'notes': 24,  # COLUMN Y
    }


class ImportItem(db.Model):
    id = db.Column('import_id', db.Integer, primary_key=True)
    sheet_name = db.Column(db.String(150))
    row = db.Column(db.Integer)

    title = db.Column(db.String(150))
    subtitle = db.Column(db.String(150))

    slug = db.Column(db.String(50))
    human_slug = db.Column(db.String(50))

    author_id = db.Column(db.Integer)
    author_first_name = db.Column(db.String(150)) #TODO: remove these in favor of the author object. Front end views should already be using Author obj
    author_last_name = db.Column(db.String(150))  #TODO: remove these in favor of the author object. Front end views should already be using Author obj

    edition = db.Column(db.String(150))
    number_of_volumes = db.Column(db.String(150))
    volume_number = db.Column(db.String(150))
    page_image = db.Column(db.String(150))
    page_num = db.Column(db.String(150))
    part_of_book = db.Column(db.String(150))
    location_in_book = db.Column(db.String(150))
    publisher = db.Column(db.String(150))
    place_of_pub = db.Column(db.String(150))
    year_of_pub = db.Column(db.String(150))
    editor_translator = db.Column(db.String(150))
    location_on_page = db.Column(db.String(150))
    line_number = db.Column(db.String(50))
    writing_implement = db.Column(db.String(150))
    language = db.Column(db.String(150))
    transcription = db.Column(db.Text)
    notes = db.Column(db.Text)
    close_image = db.Column(db.String(150))
    type = db.Column(db.String(150))
    subtype = db.Column(db.String(150))
    hand = db.Column(db.String(150))

    imported = db.Column(db.Boolean, default=False)
    raw_row = deferred(db.Column(db.Text))
    error_text = db.Column(db.Text, default=None)
    error_log = list()



    def __init__(self, sheet_name, row, import_row, raw_row):
        if len(import_row) < len(col_map)+1:
            import_row += [''] * (len(col_map)+1 - len(import_row))

        self.sheet_name = sheet_name.strip()
        self.row = row

        self.author_last_name = import_row[ col_map['author_last_name'] ].strip()
        self.author_first_name = import_row[ col_map['author_first_name'] ].strip()
        self.title = import_row[ col_map['title'] ].strip()
        self.subtitle = import_row[ col_map['subtitle'] ].strip()
        self.editor_translator = import_row[ col_map['editor_translator'] ].strip()
        self.number_of_volumes = import_row[ col_map['number_of_volumes'] ].strip()
        self.edition = import_row[ col_map['edition'] ].strip()
        self.place_of_pub = import_row[ col_map['place_of_pub'] ].strip()
        self.publisher = import_row[ col_map['publisher'] ].strip()
        self.year_of_pub = import_row[ col_map['year_of_pub'] ].strip()
        self.volume_number = import_row[ col_map['volume_number'] ].strip()
        self.location_in_book = import_row[ col_map['location_in_book'] ].strip().lower()
        self.part_of_book = import_row[ col_map['part_of_book'] ].strip()
        self.page_image = import_row[ col_map['page_image'] ].strip() #was rstrip
        self.close_image = import_row[ col_map['close_image'] ].strip()
        self.page_num = import_row[ col_map['page_num'] ].strip()
        self.location_on_page = import_row[ col_map['location_on_page'] ].strip().lower()
        self.writing_implement = import_row[ col_map['writing_implement'] ].strip().lower()
        self.line_number = import_row[ col_map['line_number'] ].strip()
        self.type = import_row[ col_map['type'] ].strip()
        self.subtype = import_row[ col_map['subtype'] ].strip()
        self.language = import_row[ col_map['language'] ].strip().lower()
        self.transcription = import_row[ col_map['transcription'] ]
        self.hand = import_row[ col_map['hand'] ].strip()
        self.notes = import_row[ col_map['notes'] ]

        self.imported = False
        self.raw_row = raw_row
        self.error_log = list()

        self.book = None
        self.author = None
        self.page = None

        self.human_slug = self.page_image.split(".")[0]
        self.slug = self.human_slug.replace(' ', '-')

        self.check_images()
        self.check_volume_fields()

        if len(self.error_log) > 0:
            self.error_text = "\n".join(self.error_log)

        if self.location_in_book == 'title page' or self.location_in_book == 'title':
            self.page_num = 'title page'
            self.page_order = 10


    def clear_errors(self):
        self.error_text = None
        self.error_log = []
        db.session.commit()

    def run_error_checks(self):
        self.clear_errors()

        self.check_images()
        self.check_volume_fields()

        if len(self.error_log) > 0:
            self.error_text = "\n".join(self.error_log)

    def run_import(self):
        if self.location_in_book == 'spine':
            return

        if self.error_text:
            self.imported = False
            return

        else:
            if self.author_exists() == False:
                self.add_author()

            if self.book_exists() == False:
                self.add_book()

            if self.page_exists() == False:
                self.add_page()


            marg = Marginalia(page_id=self.page.id, book_id=self.book.id,
                              location_on_page=self.location_on_page, line_number=self.line_number,
                              writing_implement=self.writing_implement, type=self.type, subtype=self.subtype,
                              language=self.language, transcription=self.transcription,
                              close_image=self.close_image, notes=self.notes, hand=self.hand, raw_import=self.raw_row)

            self.imported = True

            db.session.add(marg)
            db.session.commit()

    def author_exists(self):
        self.author = Author.query.filter_by(last_name=self.author_last_name, first_name=self.author_first_name).first()
        if self.author:
            return True
        else:
            return False

    def book_exists(self):
        self.book = Book.query.filter_by(slug=self.slug).first()
        if self.book:
            return True
        else:
            return False

    def page_exists(self):
        self.page = Page.query.filter_by(book_id=self.book.id, page_image=self.page_image).first()
        if self.page:
            return True
        else:
            return False

    def add_author(self):
        self.author = Author(first_name=self.author_first_name, last_name=self.author_last_name, image='', image_caption='')
        db.session.add(self.author)
        db.session.commit()

    def add_book(self):
        author_id = self.author.id
        self.book = Book(human_slug=self.human_slug,
                    title=self.title, subtitle=self.subtitle, author_id=self.author.id,
                    author_first_name=self.author_first_name, author_last_name=self.author_last_name,
                    editor_translator=self.editor_translator, edition=self.edition,
                    number_of_volumes=self.number_of_volumes, volume_number=self.volume_number,
                    part_of_book=self.part_of_book,
                    publisher=self.publisher, place_of_pub=self.place_of_pub, year_of_pub=self.year_of_pub,
                    full_text_edition_link='', period_translation_link='',
                    spine_image='',
                    raw_import=self.raw_row)
        db.session.add(self.book)
        db.session.commit()

    def add_page(self):
        last_page = Page.query.filter_by(book_id=self.book.id).order_by(sqlalchemy.desc(Page.id)).first()
        if last_page != None:
            self.page = Page(page_num=self.page_num, book_id=self.book.id,
                        location_in_book=self.location_in_book, page_image=self.page_image,
                        page_order=last_page.page_order + 10)
        else:
            self.page = Page(page_num=self.page_num, book_id=self.book.id,
                        location_in_book=self.location_in_book, page_image=self.page_image, page_order=10)
        db.session.add(self.page)
        db.session.commit()

    def check_images(self):
        if self.location_in_book == 'spine':  # dont check for spine images here, page images only
            return

        if (self.page_image == "" or self.page_image == " "):
            self.error_log.append('Slug/Page Image field blank. '.format(self.row))
            return #if page_image field blank return before image file check

        else:
            if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'pages', self.page_image + '.jpg')):
                self.error_log.append('Optimized page image not found. ')
                print('NOT FOUND:'+os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'pages', self.page_image + '.jpg'))

            if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'original', 'pages', self.page_image + '.jpg')):
                self.error_log.append('Original page image not found. ')
                print('NOT FOUND:' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'pages', self.page_image + '.jpg'))

        #if record has a close up image check for that file too
        if self.close_image:
            if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'pages', self.page_image + '.jpg')):
                self.error_log.append('Optimized close up image not found. ')
                print('NOT FOUND:' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'pages', self.page_image + '.jpg'))

            if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'original', 'pages', self.page_image + '.jpg')):
                self.error_log.append('Original close up image not found. ')
                print('NOT FOUND:' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'assets', 'pages', self.page_image + '.jpg'))

    def check_volume_fields(self):
        if self.volume_number == '':
            self.volume_number = 1

        try:
            self.volume_number = int(self.volume_number)

        except ValueError as verr:
            self.error_log.append('Volume_number not a valid number. '.format(self.row))  # do job to handle: s does not contain anything convertible to int

        except Exception as ex:
            self.error_log.append('Volume_number not a valid number. '.format(self.row))

        if self.number_of_volumes == '':
            self.number_of_volumes = 1

        try:
            self.number_of_volumes = int(self.number_of_volumes)

        except ValueError as verr:
            self.error_log.append('Number_of_volumes not a valid number. '.format(
                self.row))  # do job to handle: s does not contain anything convertible to int

        except Exception as ex:
            self.error_log.append('Number_of_volumes not a valid number. '.format(self.row))






# class ImportMapping(db.Model):
    # id = db.Column('import_id', db.Integer, primary_key=True)
    # sheet_name = db.Column(db.String(150))
    # row = db.Column(db.Integer)
