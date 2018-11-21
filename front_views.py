from flask import render_template, request, flash, redirect, url_for, jsonify, json

# import importData
from sqlalchemy.orm import joinedload, load_only, Load
from sqlalchemy.testing.plugin.plugin_base import options

from app import app, db
# from models import User, Role, Book, Page, Marginalia, Author
from models.author import Author
from models.book import Book
from models.page import Page
from models.marginalia import Marginalia
from models.import_models import ImportItem


#FRONT

@app.route('/.well-known/acme-challenge/<token_value>')
def letsencrpyt(token_value):
    with open('.well-known/acme-challenge/{}'.format(token_value)) as f:
        answer = f.readline().strip()
    return answer




#NEW METADATA
@app.route('/metadata/<list:slugs>')
def show_metadata(slugs):
    if len(slugs) > 20:
        return 'No more than 20 volumes may be queried at one time.'
    book_ids = []
    for slug in slugs:
        id_query = db.session.query(Book.id).filter_by(slug=slug).first_or_404()
        if id_query:
            book_ids.append(id_query.id)

    query = db.session.query(Marginalia).filter(Marginalia.book_id.in_((book_ids)))
    return render_template('front/metadata.html', metadata=query)





@app.route('/authors')
def show_authors():
    authors = Author.query.filter_by(public=True).order_by(Author.last_name)
    return render_template('front/authors.html', authors=authors, api_route='api/authors')


@app.route('/volumes')
def show_volumes():
    return render_template('front/volumes.html', sort='title')


@app.route('/shelf')
def show_shelf():
    # books = Book.query.all()
    # titles = db.session.query(Book).filter_by(public=True).distinct(Book.title)
    books = Book.query.filter_by(public=True).order_by(Book.title).order_by(Book.volume_number)
    query = db.session.query(Book).filter(Book.public == True).order_by(Book.volume_number)
    return render_template('front/shelf.html', books=query)



@app.route('/library/multivol/<slugs>')
def show_book_multi_vol(slugs):
    return render_template('front/volumes.html', args='?slugs='+slugs, sort='none', page_header='Selected Volumes')



@app.route('/library/<book_slug>')
def show_book(book_slug):
    book = Book.query.filter_by(slug=book_slug).first_or_404()
    page = Page.query.filter_by(book_id=book.id).first_or_404()
    return redirect(url_for('show_book_page', book_slug=book_slug, page_id=page.id))


@app.route('/library/<book_slug>/<page_id>')
def show_book_page(book_slug, page_id):
    page = Page.query.get_or_404(page_id)
    return render_template('front/page.html', book=page.book, page=page, marginalia_type_set=json.dumps(page.book.marginalia_type_set))


@app.route('/ajax/book/<book_id>')
def ajax_book(book_id):
    # book = Book.query.filter_by(slug=book_slug).first_or_404()
    book = Book.query.filter_by(id=book_id).first_or_404()
    p_list = list()
    page_order = 0
    for page in book.pages:
        p = page.serialize()
        p['page_order'] = page_order
        page_order = page_order+1
        p_list.append(p)
    return jsonify(p_list)


# @app.route('/ajax/page/<page_id>')
# def ajax_page(page_id):
#     page = Page.query.get_or_404(page_id)
#     s = page.serialize()
#     return jsonify(page.serialize())



class MarginaliaExamples():
    name = ""
    image = ""
    subtypes = []

    def __init__(self, name, image, subtypes):
        self.name = name
        self.image = image
        self.subtypes = subtypes

#static views (or mostly static)
@app.route('/')
def show_home():
    # marginalia_count = Marginalia.query.count()
    # book_count = Book.query.count()
    # author_count = db.session.query(Author).count()
    # marginalia_type_count = db.session.query(Marginalia.type).distinct()
    #
    # list = []
    # for i in marginalia_type_count:
    #     list.append(i)
    return render_template('front/static/home.html')


@app.route('/blog')
def show_blog():
    return redirect('http://blog.millmarginalia.org')

@app.route('/about')
def show_about():
    return render_template('front/static/about.html')

@app.route('/about-the-john-stuart-mill-library')
def show_about_the_john_stuart_mill_library():
    return render_template('front/static/about-the-john-stuart-mill-library.html')

@app.route('/advisory-board')
def show_advisory_board():
    return render_template('front/static/advisory-board.html')

@app.route('/citation-and-institutional-permission')
def show_citation_and_institutional_permission():
    return render_template('front/static/citation-and-institutional-permission.html')

@app.route('/credits')
def show_credits():
    return render_template('front/static/credits.html')

@app.route('/editorial-policies')
def show_editorial_policies():
    return render_template('front/static/editorial-policies.html')

@app.route('/how-to-use-this-site')
def show_how_to_use_this_site():
    return render_template('front/static/how-to-use-this-site.html')

@app.route('/institutional-collaboration')
def show_institutional_collaboration():
    return render_template('front/static/institutional-collaboration.html')

@app.route('/technical-approach')
def show_technical_approach():
    return render_template('front/static/technical-approach.html')

@app.route('/why-the-mills-and-their-marginalia')
def show_why_the_mills_and_their_marginalia():
    return render_template('front/static/why-the-mills-and-their-marginalia.html')

@app.route('/contact')
def show_contact():
    return render_template('front/static/contact.html')

@app.route('/critical-intro')
def show_critical_intro_page():
    books = Book.query.filter(Book.critical_intro != None).all()
    return render_template('front/volumes_old.html', books=books, page_subheader='Volumes with Critical Introductions')

@app.route('/critical-intro/<slug>')
def show_critical_intro(slug):
    books = Book.query.filter(Book.critical_intro == slug)
    slug_list = []
    for b in books:
        slug_list.append(b.slug)
    slugs = '+'.join(slug_list)

    return render_template('front/static/critical-intro/'+slug+'.html', books=books, args='?slugs='+slugs, sort='none')

@app.route('/marginalia-examples')
def show_marginalia_examples():
    examples = []
    examples.append(MarginaliaExamples(name='Asterisk', image='asterisk', subtypes=''))

    examples.append(MarginaliaExamples(name='Bracket', image='bracket', subtypes=[
        {'name': 'Curly', 'image': 'curly bracket'},
        {'name': 'Double', 'image': 'double bracket'},
        {'name': 'Inverted', 'image': 'inverted bracket'},
        {'name': 'Loose', 'image': 'loose bracket'},
        {'name': 'Standard', 'image': 'bracket'},

    ]))

    examples.append(MarginaliaExamples(name='Burn Mark', image='burn mark', subtypes='')) #no image?
    examples.append(MarginaliaExamples(name='Box', image='square', subtypes=''))
    examples.append(MarginaliaExamples(name='Check Mark', image='check mark', subtypes=''))
    examples.append(MarginaliaExamples(name='Circle', image='circle', subtypes=''))

    examples.append(MarginaliaExamples(name='Cross Reference', image='cross reference', subtypes=''))
    examples.append(MarginaliaExamples(name='Dash', image='dash', subtypes=''))
    examples.append(MarginaliaExamples(name='Ditto Mark', image='ditto mark', subtypes=''))
    examples.append(MarginaliaExamples(name='Doodle', image='doodle', subtypes=''))
    examples.append(MarginaliaExamples(name='Dot', image='dot', subtypes=''))
    examples.append(MarginaliaExamples(name='Double Exclamation Point', image='double exclamation point', subtypes=''))
    examples.append(MarginaliaExamples(name='Double Question Mark', image='double question mark', subtypes=''))
    examples.append(MarginaliaExamples(name='Double Underline', image='double underline', subtypes=''))
    examples.append(MarginaliaExamples(name='Downward Arrow', image='downward arrow', subtypes=''))
    examples.append(MarginaliaExamples(name='Exclamation Point', image='exclamation point', subtypes=''))

    examples.append(MarginaliaExamples(name='Excised X', image='excised x', subtypes=''))  # no image?

    examples.append(MarginaliaExamples(name='Idle Mark', image='idle mark', subtypes=''))
    examples.append(MarginaliaExamples(name='Idle Shading', image='idle shading', subtypes=''))
    examples.append(MarginaliaExamples(name='Chevron', image='left chevron', subtypes=''))
    examples.append(MarginaliaExamples(name='Musical Note', image='musical note', subtypes=''))
    examples.append(MarginaliaExamples(name='Plus Sign', image='plus sign', subtypes=''))
    examples.append(MarginaliaExamples(name='Question Mark', image='question mark', subtypes=''))

    examples.append(MarginaliaExamples(name='Score', image='score', subtypes=[
        {'name': 'Corrugated', 'image': 'corrugated score'},
        {'name': 'Dotted', 'image': 'dotted score'},
        {'name': 'Double', 'image': 'double score'},
        {'name': 'Standard', 'image': 'score'},
        {'name': 'Tailed', 'image': 'tailed score'},
        {'name': 'Tallied', 'image': 'tallied score'},
        {'name': 'Triple', 'image': 'triple score'},
    ]))


    examples.append(MarginaliaExamples(name='Scratchthrough', image='scratchthrough', subtypes=''))
    examples.append(MarginaliaExamples(name='Slash', image='slash', subtypes=''))
    examples.append(MarginaliaExamples(name='Slashthrough', image='slashthrough', subtypes=''))
    examples.append(MarginaliaExamples(name='Smudge', image='smudge', subtypes=''))

    examples.append(MarginaliaExamples(name='Squiggle', image='squiggle', subtypes=''))
    examples.append(MarginaliaExamples(name='Strikethrough', image='strikethrough', subtypes=''))

    examples.append(MarginaliaExamples(name='Text', image='text', subtypes=[
        {'name': 'Authorial Inscription', 'image': 'text SUBTYPE - authorial inscription'},
        {'name': 'Copyedit', 'image': 'copyedit'},
        {'name': 'Date', 'image': "text SUBTYPE - date"},
        {'name': 'Editorial Inscription', 'image': 'text SUBTYPE - editorial inscription'},
        {'name': 'Equation', 'image': "text SUBTYPE - equation"},
        {'name': 'Numbers', 'image': 'text SUBTYPE - numbers'},
        {'name': 'Record of Original Publication Information',
         'image': "text SUBTYPE - record of original publication information"},
        {'name': 'Revision of Original', 'image': "text SUBTYPE - revision of original"},
        {'name': 'Notation of Error', 'image': 'text SUBTYPE - notation of error'},  #no image?
        # {'name': 'Punctuation', 'image': "text SUBTYPE - punctuation"},
    ]))

    examples.append(MarginaliaExamples(name='Tilde', image='tilde', subtypes=''))
    examples.append(MarginaliaExamples(name='Trace Transfer', image='trace transfer', subtypes='')) #no image?
    examples.append(MarginaliaExamples(name='Triangle', image='triangle', subtypes=''))
    examples.append(MarginaliaExamples(name='Underlining', image='underlining', subtypes=''))
    examples.append(MarginaliaExamples(name='Unfilled Matrix', image='unfilled matrix', subtypes=''))
    examples.append(MarginaliaExamples(name='X Mark', image='X mark', subtypes=''))

    examples.append(MarginaliaExamples(name='Ink Blot', image='ink blot', subtypes=''))  #no image?
    examples.append(MarginaliaExamples(name='Footnote Mark', image='footnote mark', subtypes=''))  #no image?
    examples.append(MarginaliaExamples(name='Ampersand', image='ampersand', subtypes=''))  #no image?
    examples.append(MarginaliaExamples(name='Word Map', image='word map', subtypes=''))   #no image?

    return render_template('front/static/marginalia-examples.html', examples=examples)



@app.route('/OLD/library/multivol/<spine_slug>')
def show_book_multi_vol_OLD(spine_slug):
    query = db.session.query(Book).filter(Book.spine_image == spine_slug + ".png").order_by(Book.volume_number)

    books_json = []
    title_set = set()
    for book in query:
        vol = {
            'page_count': book.page_count,
            'marginalia_count': book.marginalia_count,
            'link': book.slug
        }

        if book.part_of_book:
            vol['volume_label'] = book.part_of_book

        else:
            vol['volume_label'] = 'Volume '+str(book.volume_number)

        if book.title in title_set:
            for i in books_json:
                if i['title'] == book.title:
                    i['volumes'].append(vol)

        else:
            title_set.add(book.title)

            j = {
                'title': book.title,
                'subtitle': book.subtitle,
                'author': {
                    'first_name': book.author_first_name,
                    'last_name': book.author.last_name
                }
            }

            if book.number_of_volumes and int(book.number_of_volumes) > 1:
                j['volumes'] = []
                j['volumes'].append(vol)

            else:
                j['page_count'] = book.page_count
                j['marginalia_count'] = book.number_of_marginalia
                j['link'] = book.link

            books_json.append(j)

    return render_template('front/volumes_old.html', books=query, multivol_view=True, books_json=books_json)

