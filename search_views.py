from flask import request, jsonify, render_template, json
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy import tuple_

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
            types_list = []

            for item in types:
                item = str.strip(item)
                if ':' in item:
                    item_split = str.split(item, ':')
                    types_list.append([item_split[0], item_split[1]])
                else:
                    types_list.append([item, ''])

            results = results.filter(tuple_(Marginalia.type, Marginalia.subtype).in_(types_list))

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
        marginalia_type_set = ['ampersand', 'asterisk', 'box', 'bracket:close', 'bracket:curly', 'bracket:double',
                               'bracket:inverted', 'bracket:loose', 'bracket:open', 'bracket:standard', 'check mark',
                               'chevron', 'circle', 'dash', 'ditto mark', 'doodle', 'dot', 'double dash',
                               'double exclamation point', 'double plus sign', 'double question mark', 'double slash',
                               'double underline', 'downward arrow', 'excised x', 'exclamation point', 'footnote mark',
                               'idle mark', 'idle shading', 'ink blot', 'musical note', 'over-tracing', 'plus sign',
                               'question mark', 'quotation marks', 'score:bracketing', 'score:corrugated',
                               'score:dotted', 'score:double', 'score:scratched', 'score:standard', 'score:tailed',
                               'score:tallied', 'score:triple', 'scratchthrough', 'slash', 'slashthrough', 'smudge',
                               'squiggle', 'strikethrough', 'text', 'text:authorial inscription', 'text:copyedit',
                               'text:date', 'text:editorial correction', 'text:editorial inscription', 'text:equation',
                               'text:numbers', 'text:record of original publication information',
                               'text:revision of original', 'tilde', 'trace transfer', 'triangle', 'underlining',
                               'unfilled matrix', 'upturned dash', 'upward arrow', 'word map', 'X mark']

        authors = Author.query.order_by(Author.last_name).all()
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
