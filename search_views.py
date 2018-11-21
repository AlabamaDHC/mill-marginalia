from flask import request, jsonify, render_template, json
from sqlalchemy import or_

# from models import Marginalia, Book, Author
from models.author import Author
from models.book import Book
from models.page import Page
from models.marginalia import Marginalia
from models.import_models import ImportItem


from app import app, db


class SearchItemResults():
    def __init__(self, marginalia):
        self.id = marginalia.id

        self.page_id = marginalia.page.id
        self.page_num = marginalia.page.page_num

        self.type = marginalia.type
        self.hand = marginalia.hand
        self.subtype = marginalia.subtype
        self.line_number = marginalia.line_number
        self.location_on_page = marginalia.location_on_page
        self.transcription = marginalia.transcription
        self.display_class = marginalia.display_class

        self.book_id = marginalia.book.id
        self.book_slug = marginalia.book.slug
        self.book_title = marginalia.book.title
        self.book_subtitle = marginalia.book.subtitle
        self.part_of_book = marginalia.book.part_of_book
        self.volume_number = marginalia.book.volume_number

        self.author_id = marginalia.book.author.id
        self.author_first_name = marginalia.book.author.first_name
        self.author_last_name = marginalia.book.author.last_name

    def serialize(self):
        json = {
            'hand': self.hand,
            'type': self.type,
            'subtype': self.subtype,
            'line_number': self.line_number,
            'location_on_page': self.location_on_page,
            'transcription': self.transcription,
            'display_class': self.display_class,
            'page': {
                'id': self.page_id,
                'num': self.page_num
            }
        }
        return json

@app.route('/search', methods=['GET', 'POST'])
def basic_search():
    if request.method == 'POST':
        data = json.loads(request.data)
        limit = 100

        results = Marginalia.query

        if 'offset' in data:
            if data['offset'] <= 0:
                data['offset'] = 0
            offset = data['offset']*limit

        else:
            offset = 0*limit

        if 'types' in data and len(data['types']) > 0:
            types = data['types']

            subtypes = ['Editorial Correction','Capitalization Change', 'Layout Change','Punctuation',
                        'Punctuation Change','Spelling Correction','Textual Revision','Word Addition',
                        'Word Change','Word Excision','Authorial Inscription', 'Numbers', 'Textual Correction',
                        'Editorial Inscription', 'Date', 'Equation', 'Numbers', 'Punctuation',
                        'Record of Original Publication Information', 'Revision of Original']
            results = results.filter(or_(Marginalia.type.in_(types), Marginalia.subtype.in_(types)))

        if 'authors' in data and len(data['authors']) > 0:
            authors = data['authors']
            books = Book.query.filter(Book.author_id.in_(authors))
            book_list = []
            for b in books:
                book_list.append(b.id)
            # results = results.join(Marginalia.book)
            results = results.filter(Marginalia.book_id.in_(book_list))

        if 'books' in data and len(data['books']) > 0:
            books = data['books']
            results = results.filter(Marginalia.book_id.in_(books))

        if 'hand' in data and len(data['hand']) > 0:
            hand = data['hand']
            results = results.filter(Marginalia.hand.in_(hand))

        results_list = {}
        resp = {'results_count': results.count(), 'offset': offset/limit, 'results': results_list}
        results = results.limit(limit).offset(offset)

        for item in results:
            i = SearchItemResults(item).serialize()
            if item.book.id not in results_list:
                results_list[item.book.id] = {
                    'id': item.book.id,
                    'slug': item.book.slug,
                    'title': item.book.title,
                    'subtitle': item.book.subtitle,
                    'part_of_book': item.book.part_of_book,
                    'volume_number': item.book.volume_number,
                    'author': {
                        'id': item.book.author_id,
                        'first_name': item.book.author_first_name,
                        'last_name': item.book.author_last_name
                    },
                    'results': [i]
                }
            else:
                results_list[item.book.id]['results'].append(i)


        return jsonify(resp)

    if request.method == 'GET':
        marginalia_type_set = ['asterisk', 'bracket', 'brackets', 'check mark', 'circle', 'copyedit', 'editorial correction',
            'capitalization change', 'layout change', 'punctuation', 'punctuation change',
            'spelling correction', 'textual revision', 'word addition', 'word change', 'word excision',
            'corrugated score', 'cross reference', 'curly bracket', 'dash', 'ditto mark', 'doodle',
            'dot', 'dotted score', 'double bracket', 'double exclamation point', 'double question mark',
            'double score', 'double underline', 'downward arrow', 'exclamation point', 'idle mark',
            'idle shading', 'inverted bracket', 'left chevron', 'loose bracket', 'musical note',
            'plus sign', 'question mark', 'score', 'scratchthrough', 'slash', 'slashthrough', 'smudge',
            'square', 'squiggle', 'strikethrough', 'tailed score', 'text', 'authorial inscription',
            'numbers', 'textual correction', 'editorial inscription', "text", 'date',
            'equation', 'numbers', 'punctuation', 'record of original publication information',
            'revision of original', 'tilde', 'triangle', 'triple score', 'underlining', 'unfilled matrix',
            'x mark', 'tallied score']

        authors = Author.query.all()
        authors_list = []
        for a in authors:
            authors_list.append({'name': a.first_name + ' ' + a.last_name, 'id': a.id})

        books = Book.query.all()
        books_list = []
        for b in books:
            if b.part_of_book:
                books_list.append({'title': b.title + ' ' + b.subtitle + ' (' + b.part_of_book + ')', 'id': b.id})

            elif b.volume_number:
                books_list.append({'title': b.title + ' ' + b.subtitle + ' (Vol ' + str(b.volume_number) + ')', 'id': b.id})

            else:
                books_list.append({'title': b.title + ' ' + b.subtitle, 'id': b.id})


        hand = db.session.query(Marginalia.hand).distinct()
        hand_list = []
        for h in hand:
            if h.hand != '':
                hand_list.append(h.hand)

        return render_template('front/search.html', marginalia_type_set=json.dumps(marginalia_type_set), authors_list=json.dumps(authors_list), books_list=json.dumps(books_list), hand_list=json.dumps(hand_list))
