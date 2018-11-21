from app import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred

class Marginalia(db.Model):
    id = db.Column('marg_id', db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.page_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'))

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

    raw_import = deferred(db.Column(db.Text))

    # rawRecord
    # importSrcFile
    # importOrder
    #
    # pageImg
    # closeImg
    #
    # inBook
    # lineNum
    # onPage
    # pageNum
    # partOfBook
    #
    # recordType
    # writingImplement
    # transcription
    #hand
    # notes
    #
    # type
    # top
    # main
    # sub
    # language
    # hand

    def __init__(self, page_id, book_id, location_on_page, line_number,
                 writing_implement, type, subtype, language, transcription,
                 close_image, notes, hand, raw_import):
        self.page_id = page_id
        self.book_id = book_id

        self.location_on_page = location_on_page
        self.line_number = line_number
        self.writing_implement = writing_implement
        self.type = type
        self.subtype = subtype
        self.language = language
        self.transcription = transcription
        self.close_image = close_image
        self.hand = hand
        self.notes = notes #PRIVATE
        self.raw_import = raw_import #PRIVATE

    @hybrid_property
    def display_transcription(self):
        display = "" + self.transcription.replace('/', '<br>').replace('"', '\"')
        return display

    @hybrid_property
    def display_class(self):
        display_class = self.type.replace("'", "").replace("(", "").replace(")", "").replace(" ", "-").replace(" ", "-").lower();
        return display_class

    def serialize(self, includeRelations=False, forAJAX=True, includePrivate=False, imageRoot='assets/pages/', imageExt='.jpg'):
        json = {}

        if forAJAX:
            if self.type and self.type != "":
                json['type'] = self.type
                # json['display_class'] = self.display_class

            if self.subtype and self.subtype != "":
                json['subtype'] = self.subtype

            if self.transcription and self.transcription != "":
                json['transcription'] = self.display_transcription

            if self.close_image and self.close_image != "":
                json['close_image'] = self.close_image
                # json['close_image'] = url_for('static', filename=imageRoot + self.close_image + imageExt)

            if self.line_number and self.line_number != "":
                json['line_number'] = self.line_number

            if self.hand and self.hand != "" and self.hand != " ":
                json['hand'] = self.hand

            return json


        if includeRelations:
            json['page_id'] = self.page_id
            json['book_id'] = self.book_id

        if includePrivate:
            json['notes'] = self.notes
            json['raw_import'] = self.raw_import

        return json

