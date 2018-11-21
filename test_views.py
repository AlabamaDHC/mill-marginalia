from copy import deepcopy

import flask
from flask import render_template
from flask_security import login_required
from flask_sqlalchemy import model
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, make_transient

from app import app, db

from models.author import Author
from models.book import Book
from models.page import Page
from models.marginalia import Marginalia

import os.path

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean



# There is probably a better, less crude way to do this but it was done in a hurry and it seems to work.
# I was using this to copy data from the Staging to Production only. If you want to copy from Testing to production
# I suggest doing a sql dump or using something like DataGrip
@app.route('/copy_db')
def copy_db():
    # src_engine = app.config['SQLALCHEMY_DATABASE_URI']
    # dest_engine = app.config['SQLALCHEMY_BINDS']['TEST_STAGING']

    src_engine = create_engine('mysql+pymysql://root@localhost/mill')
    dest_engine = create_engine('mysql+pymysql://root@localhost/mill_staging?charset=utf8')

    metadata = MetaData(bind=dest_engine)

    # Drop and create new tables. This will delete all data in destination database!
    tables = ['marginalia', 'page', 'book', 'author', 'user']
    for t in tables:
        table = Table(t, metadata, autoload=True, autoload_with=src_engine)

        try:
            table.drop(dest_engine)
        except:
            print("Table {} already doesn't exists", t)


    for t in reversed(tables):
        table = Table(t, metadata, autoload=True, autoload_with=src_engine)
        table.create(dest_engine)


    Session = sessionmaker()
    dest_session = Session(bind=dest_engine)
    # src_session = Session(bind=dest_engine)

    #copy all data to new tables in destination database
    objects = [Author, Book, Page, Marginalia]
    for obj in objects:
        query = db.session.query(obj).all()
        for item in query:
            make_transient(item)
            # item._oid = None          not needed?
            dest_session.add(item)
        dest_session.commit()
    return 'Done'





#only util at this point. not used anywhere in site
@app.route('/test/metadata/<book_id>')
def test_metadata_vol(book_id):
    query = db.session.query(Marginalia).filter(Marginalia.book_id.in_((ids)))
    return render_template('front/metadata.html', metadata=query)


#only util at this point. not used anywhere in site
@app.route('/test/metadata/<book_id>')
def test_metadata_file(book_id):
    query = db.session.query(Marginalia).filter_by(book_id=book_id)
    results = ''
    for item in query:
        raw_import = item.raw_import.replace('\t', ';') + "<br>"
        results = results + raw_import

    # resp = flask.make_response(results)
    # resp.content_type = "text/csv "
    # return resp
    # return repr(results)
    return render_template('front/metadata.html', metadata=query)


#only util at this point. not used anywhere in site
@app.route('/test/metadata/multi/<list:slugs>')
def test_metadata_multi(slugs):
    book_ids = []
    for slug in slugs:
        id_query = db.session.query(Book.id).filter_by(slug=slug).first_or_404()
        if id_query:
            book_ids.append(id_query.id)

    query = db.session.query(Marginalia).filter(Marginalia.book_id.in_((book_ids)))
    return render_template('front/metadata.html', metadata=query)


#only util at this point. not used anywhere in site
@app.route('/list/vols/<list:slugs>')
def list_vols_by_slug(slugs):
    books = []
    for slug in slugs:
        book = Book.query.filter_by(slug=slug).first_or_404()
        if book:
            books.append(book)
    return render_template('front/volumes.html', books=books, page_subheader='Selected Volumes')


#only util at this point. not used anywhere in site
@app.route('/list/authors/<list:last_names>')
def list_authors_by_last_name(last_names):
    authors = []
    for name in last_names:
        author = Author.query.filter_by(last_name=name).first_or_404()
        if author:
            authors.append(author)
    return render_template('front/authors.html', authors=authors)



@app.route('/check_all')
@login_required
def check_all():
    authors_log = check_authors()
    authors = '<h1>{0}</h1><br><h2>Errors: {1}</h2>{2}<hr><br><br>'.format('Authors', len(authors_log)-8, "".join(authors_log))

    books_log = check_books()
    books = '<h1>{0}</h1><br><h2>Errors: {1}</h2>{2}<hr><br><br>'.format('Books', len(books_log)-8, "".join(books_log))

    pages_log = check_pages()
    pages = '<h1>{0}</h1><br><h2>Errors: {1}</h2>{2}<hr><br><br>'.format('Pages', len(pages_log)-8, "".join(pages_log))

    marginalia_log = check_marginalia()
    marginalia = '<h1>{0}</h1><br><h2>Errors: {1}</h2>{2}<hr><br><br>'.format('Marginalia', len(marginalia_log)-8, "".join(marginalia_log))


    return authors + books + pages + marginalia + '<style>' \
                                                  'table, th, td { border: 1px solid black; border-collapse: collapse; } ' \
                                                  'th { text-align: left;} ' \
                                                  '.color-header { min-width:20px } ' \
                                                  '.color-cell { min-width: 20px;} ' \
                                                  '.color-cell.red { background-color:red;} ' \
                                                  '.color-cell.yellow { background-color:yellow;} ' \
                                                  '.color-cell.orange { background-color:orange;} ' \
                                                  '</style>'


@app.route('/check_marginalia')
@login_required
def check_marginalia():
    table_log = ['<table>', '<tr>', '<th class="marg-color-header"></th>', '<th class="marg-id-header">ID</th>',
                 '<th class="marg-page-id-header">Page ID</th>','<th class="marg-name-header">Type</th>',
                 '<th class="marg-name-header">Line Num</th>', '<th class="marg-error-header">Error</th>', '</tr>']
    marginalia = Marginalia.query.all()

    for marg in marginalia:
        all_fields = ['id','page_id','book_id', 'location_on_page', 'line_number', 'writing_implement', 'language',
                      'transcription', 'close_image', 'type', 'subtype'] #'raw_import', 'notes'

        critical_fields = ['id', 'page_id', 'book_id', 'type']  # 'raw_import', 'notes'

        for field in critical_fields:
            value = getattr(marg, field)
            if value == "" or value == " ":
                table_log.append('<tr>'
                                 '<td class="color-cell {0}"></td>' \
                                 '<td class="marg-id-cell">{1}</td>' \
                                 '<td class="marg=page-id-cell">{2}</td>' \
                                 '<td class="marg-type-cell">{3}</td>' \
                                 '<td class="marg=line-num-cell">{4}</td>' \
                                 '<td class="marg-error-cell">Blank {5} field</td>' \
                                 '</tr>'.format('yellow', marg.id, marg.page_id, marg.type, marg.line_number,field))

                if field == "type":
                    if value == "" or value == " ":
                        table_log.pop()
                        table_log.append('<tr>' \
                                        '<td class="color-cell {0}"></td>' \
                                        '<td class="marg-id-cell">{1}</td>' \
                                        '<td class="marg=page-id-cell">{2}</td>' \
                                        '<td class="marg-type-cell">{3}</td>' \
                                        '<td class="marg=line-num-cell">{4}</td>' \
                                        '<td class="marg-error-cell">Blank {5} field</td>' \
                                        '</tr>'.format('red', marg.id, marg.page_id, marg.book.title, marg.type, field))

                # log.append('Author <{0}>: Blank {1} field'.format(book.id, field))

    table_log.append('</table>'
                     '<style>'
                     '.marg-id-header{ padding-left: 15px } '
                     '.marg-id-cell{width:30px; padding: 1px 15px;} '
                     '.marg-name-cell{width:175px;}  '
                     '.marg-error-cell{width:300px; }</style>')

    return table_log



@app.route('/check_pages')
@login_required
def check_pages():
    table_log = ['<table>', '<tr>', '<th class="page-color-header"></th>', '<th class="page-id-header">ID</th>',
                 '<th class="page-name-header">Name</th>', '<th class="page-error-header">Error</th>', '</tr>']
    pages = Page.query.all()

    for page in pages:
        all_fields = ['id','page_num','book_id', 'location_in_book', 'part_of_book', 'page_image', 'page_order']

        critical_fields = ['id', 'page_num', 'book_id', 'page_image', 'page_order']

        for field in critical_fields:
            value = getattr(page, field)
            if value == "" or value == " ":
                table_log.append('<tr>'
                                 '<td class="color-cell {0}"></td>'
                                 '<td class="page-id-cell">{1}</td>'
                                 '<td class="page-name-cell">{2} {3}</td>'
                                 '<td class="page-error-cell">Blank {4} field</td>'
                                 '</tr>'.format('red', page.id, page.page_num, page.page_image, field))
                # log.append('Author <{0}>: Blank {1} field'.format(book.id, field))


        if not os.path.exists( os.path.join( os.path.dirname(__file__),'static','assets', 'pages', page.page_image+'.jpg') ):
            if os.path.exists( os.path.join(os.path.dirname(__file__), 'static', 'assets', 'original', 'pages', page.page_image + '.jpg')):
                table_log.append('<tr>'
                                 '<td class="color-cell {0}"></td>'
                                 '<td class="book-id-cell">{1}</td>'
                                 '<td class="book-name-cell">{2}</td>'
                                 '<td class="book-error-cell">Original page image file exists but optimized copy does not.</td>'
                                 '</tr>'.format('red', page.id, os.path.join(os.path.dirname(__file__), 'static', 'assets', 'original', 'pages', page.page_image + '.jpg')))
            else:
                table_log.append('<tr>'
                             '<td class="color-cell {0}"></td>'
                             '<td class="book-id-cell">{1}</td>'
                             '<td class="book-name-cell">{2}</td>'
                             '<td class="book-error-cell">Neither original or optimized page image file exists</td>'
                             '</tr>'.format('red', page.id, os.path.join( os.path.dirname(__file__),'static','assets', 'pages', page.page_image+'.jpg')))




    table_log.append('</table><style>'
                     '.page-id-header{ padding-left: 15px } '
                     '.page-id-cell{width:30px; padding: 1px 15px;} '
                     '.page-name-cell{width:175px;}  '
                     '.page-error-cell{width:300px; }</style>')
    return table_log


@app.route('/check_books')
@login_required
def check_books():
    table_log = ['<table>', '<tr>', '<th class="book-color-header"></th>', '<th class="book-id-header">ID</th>',
                 '<th class="book-name-header">Name</th>', '<th class="book-error-header">Error</th>', '</tr>']
    books = Book.query.all()

    for book in books:
        all_fields = ['id','slug','human_slug', 'spine_image', 'title', 'subtitle', 'author_id', 'author_first_name',
                      'author_last_name', 'editor_translator', 'edition', 'number_of_volumes', 'volume_number', 'publisher',
                      'place_of_pub', 'year_of_pub', 'full_text_edition_link', 'period_translation_link']

        critical_fields = ['id','slug','human_slug', 'spine_image', 'author_id']

        for field in critical_fields:
            value = getattr(book, field)
            if value == "" or value == " ":
                table_log.append('<tr>'
                                 '<td class="color-cell {0}"></td>'
                                 '<td class="book-id-cell">{1}</td>'
                                 '<td class="book-name-cell">{2} {3}. Ed {4}</td>'
                                 '<td class="book-error-cell">Blank {5} field</td>'
                                 '</tr>'.format('red', book.id, book.title, book.subtitle, book.edition, field))

        if book.number_of_volumes and book.number_of_volumes != '' and book.number_of_volumes != ' ' and (book.volume_number == '' or book.volume_number == ' '):
            table_log.append('<tr>'
                             '<td class="color-cell {0}"></td>'
                             '<td class="book-id-cell">{1}</td>'
                             '<td class="book-name-cell">{2} {3}. Ed {4}</td>'
                             '<td class="book-error-cell">Has multiple volumes but volume_number field blank</td>'
                             '</tr>'.format('red', book.id, book.title, book.subtitle, book.edition))

        if book.pages.count() <= 1:
            table_log.append('<tr>'
                             '<td class="color-cell {0}"></td>'
                             '<td class="book-id-cell">{1}</td>'
                             '<td class="book-name-cell">{2} {3}. Ed {4}</td>'
                             '<td class="book-error-cell">Book has 1 or less pages. Check for typo in book slug</td>'
                             '</tr>'.format('red', book.id, book.title, book.subtitle, book.edition))


        if not os.path.exists( os.path.join( os.path.dirname(__file__),'static','assets', 'spines', book.spine_image) ):
            table_log.append('<tr>'
                             '<td class="color-cell {0}"></td>'
                             '<td class="book-id-cell">{1}</td>'
                             '<td class="book-name-cell">{2}</td>'
                             '<td class="book-error-cell">Spine image file does not exist</td>'
                             '</tr>'.format('red', book.id, os.path.join( os.path.dirname(__file__),'static','assets', 'spines', book.spine_image )))




    table_log.append('</table><style>'
                     '.book-id-header{ padding-left: 15px } '
                     '.book-id-cell{width:30px; padding: 1px 15px;} '
                     '.book-name-cell{width:750px;}  '
                     '.book-error-cell{width:300px; }</style>')

    return table_log


@app.route('/check_authors')
@login_required
def check_authors():
    table_log = ['<table>', '<tr>', '<th class="author-color-header"></th>', '<th class="author-id-header">ID</th>',
                 '<th class="author-name-header">Name</th>', '<th class="author-error-header">Error</th>', '</tr>']
    authors = Author.query.all()

    for author in authors:
        fields = ['id', 'first_name', 'last_name', 'image', 'image_caption']
        for field in fields:
            value = getattr(author, field)
            if value == "" or value == " ":
                table_log.append('<tr>'
                                    '<td class="color-cell {0}"></td>'
                                    '<td class="author-id-cell">{1}</td>'
                                    '<td class="author-name-cell">{2} {3}</td>'
                                    '<td class="author-error-cell">Blank {4} field</td>'
                                    '</tr>'.format('red', author.id, author.first_name, author.last_name, field ))

        if author.books.count() == 0:
            table_log.append('<tr>'
                             '<td class="color-cell {0}"></td>'
                             '<td class="author-id-cell">{1}</td>'
                             '<td class="author-name-cell">{2} {3}</td>'
                             '<td class="author-error-cell">Has no books linked</td>'
                             '</tr>'.format('red', author.id, author.first_name, author.last_name))

    table_log.append('</table>'
                     '<style>'
                     'th {text-align: left;} '
                     '.color-header{ width:20px } '
                     '.author-id-header{ padding-left: 15px } '
                     '.color-cell{width: 20px;} '
                     '.color-cell.red{background-color:red;} '
                     '.author-id-cell{width:30px; padding: 1px 15px;} '
                     '.author-name-cell{width:175px;}  '
                     '.author-error-cell{width:300px; }</style>')
    return table_log








#Books in July 2015 & July 2016 sheets
@app.route('/import_books_2015_2016')
def import_books_2015_2016():
    b1 = Book(human_slug='RWE E', title='Essays', subtitle='', author_id='1', author_first_name='R. W.',
              author_last_name='Emerson', editor_translator='', edition='1st', number_of_volumes='', volume_number='',
              publisher='James Fraser', place_of_pub='London', year_of_pub='1841', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b2 = Book(human_slug='RWE E2', title='Essays', subtitle='Second Series', author_id='1', author_first_name='R. W.',
              author_last_name='Emerson', editor_translator='', edition='1st', number_of_volumes='', volume_number='',
              publisher='John Chapman', place_of_pub='London', year_of_pub='1844', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b3 = Book(human_slug='TC SR', title='Sartor Resartus', subtitle='', author_id='2', author_first_name='Thomas',
              author_last_name='Carlyle', editor_translator='', edition='2nd', number_of_volumes='', volume_number='',
              publisher='James Munroe and Company', place_of_pub='Boston', year_of_pub='1837', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b4 = Book(human_slug='TC C', title='Chartism', subtitle='', author_id='2', author_first_name='Thomas',
              author_last_name='Carlyle', editor_translator='', edition='1st', number_of_volumes='', volume_number='',
              publisher='James Fraser', place_of_pub='London', year_of_pub='1840', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b5 = Book(human_slug='TC C', title='Chartism', subtitle='', author_id='2', author_first_name='Thomas',
              author_last_name='Carlyle', editor_translator='', edition='', number_of_volumes='', volume_number='',
              publisher='James Fraser', place_of_pub='London', year_of_pub='1840', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b6 = Book(human_slug='TC H', title='On Heroes, Hero-Worship, and The Heroic in History', subtitle='', author_id='2',
              author_first_name='Thomas', author_last_name='Carlyle', editor_translator='', edition='1st',
              number_of_volumes='', volume_number='', publisher='James Fraser', place_of_pub='London',
              year_of_pub='1841', spine_image='!!!', full_text_edition_link='', period_translation_link='',
              raw_import='!!!')
    b7 = Book(human_slug='TC H', title='On Heroes, Hero-Worship and the Heroic in History ', subtitle='', author_id='2',
              author_first_name='Thomas', author_last_name='Carlyle', editor_translator='', edition='1st',
              number_of_volumes='', volume_number='', publisher='James Fraser', place_of_pub='London',
              year_of_pub='1841', spine_image='!!!', full_text_edition_link='', period_translation_link='',
              raw_import='!!!')
    b8 = Book(human_slug='TC LDP', title='Latter-Day Pamphlets', subtitle='', author_id='2', author_first_name='Thomas',
              author_last_name='Carlyle', editor_translator='', edition='1st', number_of_volumes='', volume_number='',
              publisher='Chapman and Hall', place_of_pub='London', year_of_pub='1850', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b9 = Book(human_slug='TC LDP', title='Latter-Day Pamphlets', subtitle='', author_id='2', author_first_name='Thomas',
              author_last_name='Carlyle', editor_translator='', edition='1st', number_of_volumes='', volume_number='',
              publisher='Chapman and Hall', place_of_pub='London', year_of_pub='1850', spine_image='!!!',
              full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b10 = Book(human_slug='TC JS', title='The Life of John Sterling', subtitle='', author_id='2',
               author_first_name='Thomas', author_last_name='Carlyle', editor_translator='', edition='1st',
               number_of_volumes='', volume_number='', publisher='Chapman and Hall', place_of_pub='London',
               year_of_pub='1851', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b11 = Book(human_slug='TC PP', title='Past and Present', subtitle='', author_id='2', author_first_name='Thomas',
               author_last_name='Carlyle', editor_translator='', edition='1st', number_of_volumes='', volume_number='',
               publisher='Chapman and Hall', place_of_pub='London', year_of_pub='1843', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b12 = Book(human_slug='HM AL', title='Ancient Law',
               subtitle='Its Connection with the Early History of Society, and Its Relation to Modern Ideas',
               author_id='3', author_first_name='Henry Sumner', author_last_name='Maine', editor_translator='',
               edition='1st', number_of_volumes='', volume_number='', publisher='John Murray', place_of_pub='London',
               year_of_pub='1861', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b13 = Book(human_slug='JS ET 1', title='Essays and Tales', subtitle='', author_id='4', author_first_name='John',
               author_last_name='Sterling', editor_translator='Julius Charles Hare', edition='1st',
               number_of_volumes='2', volume_number='1', publisher='John W. Parker', place_of_pub='London',
               year_of_pub='1848', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b14 = Book(human_slug='JS ET 2', title='Essays and Tales', subtitle='', author_id='4', author_first_name='John',
               author_last_name='Sterling', editor_translator='Julius Charles Hare', edition='1st',
               number_of_volumes='2', volume_number='2', publisher='John W. Parker', place_of_pub='London',
               year_of_pub='1848', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b15 = Book(human_slug='AS DL', title='A Course of Lectures on Dramatic Art and Literature', subtitle='',
               author_id='5', author_first_name='Augustus William', author_last_name='Schlegel',
               editor_translator='John Black, A.J.W. Morrison', edition='1st English', number_of_volumes='',
               volume_number='', publisher='Henry G. Bohn', place_of_pub='London', year_of_pub='1846',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b16 = Book(human_slug='CD DM 1', title='The Descent of Man', subtitle='and Selection in Relation to Sex',
               author_id='6', author_first_name='Charles', author_last_name='Darwin', editor_translator='',
               edition='1st', number_of_volumes='2', volume_number='1', publisher='John Murray', place_of_pub='London',
               year_of_pub='1871', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b17 = Book(human_slug='CD DM 2', title='The Descent of Man', subtitle='and Selection in Relation to Sex',
               author_id='6', author_first_name='Charles', author_last_name='Darwin', editor_translator='',
               edition='1st', number_of_volumes='2', volume_number='2', publisher='John Murray', place_of_pub='London',
               year_of_pub='1871', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b18 = Book(human_slug='RC V', title='Vestiges of the Natural History of Creation', subtitle='', author_id='7',
               author_first_name='Robert', author_last_name='Chambers', editor_translator='', edition='1st',
               number_of_volumes='', volume_number='', publisher='John Churchill', place_of_pub='London',
               year_of_pub='1844', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b19 = Book(human_slug='RB W', title='The Works of Robert Burns',
               subtitle='to which is prefixed A Life of the Author', author_id='8', author_first_name='Robert',
               author_last_name='Burns', editor_translator='James Currie', edition='1st', number_of_volumes='',
               volume_number='', publisher='Thomas Davison', place_of_pub='London', year_of_pub='1824',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b20 = Book(human_slug='',
               title='The Works of Robert Burns, to which Is prefixed a life of the Author, by James Currie M.D.',
               subtitle='', author_id='8', author_first_name='Robert', author_last_name='Burns', editor_translator='',
               edition='[new edition]', number_of_volumes='', volume_number='', publisher='Thomas Tegg [plus others]',
               place_of_pub='London', year_of_pub='1824', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b21 = Book(human_slug='RB W L', title='The Works of Robert Burns',
               subtitle='to which is prefixed A Life of the Author', author_id='8', author_first_name='Robert',
               author_last_name='Burns', editor_translator='James Currie', edition='1st', number_of_volumes='',
               volume_number='', publisher='Thomas Davison', place_of_pub='London', year_of_pub='1824',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b22 = Book(human_slug='RB W C',
               title='The Works of Robert Burns, to which Is prefixed a life of the Author, by James Currie M.D.',
               subtitle='', author_id='8', author_first_name='Robert', author_last_name='Burns', editor_translator='',
               edition='[new edition]', number_of_volumes='', volume_number='', publisher='Thomas Tegg [plus others]',
               place_of_pub='London', year_of_pub='1824', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b23 = Book(human_slug='RB W C', title='The Works of Robert Burns',
               subtitle='to which is prefixed A Life of the Author', author_id='8', author_first_name='Robert',
               author_last_name='Burns', editor_translator='James Currie', edition='1st', number_of_volumes='',
               volume_number='', publisher='Thomas Davison', place_of_pub='London', year_of_pub='1824',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b24 = Book(human_slug='JM EB', title='Edmund Burke', subtitle='A Historical Study', author_id='9',
               author_first_name='John', author_last_name='Morley', editor_translator='', edition='1st',
               number_of_volumes='', volume_number='', publisher='Macmillan and Co.', place_of_pub='London',
               year_of_pub='1867', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b25 = Book(human_slug='JM EB', title='Edmund Burke', subtitle='A Historical Study', author_id='9',
               author_first_name='John', author_last_name='Morley', editor_translator='', edition='1st',
               number_of_volumes='', volume_number='', publisher='Macmillan and Co.', place_of_pub='London',
               year_of_pub='1867', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b26 = Book(human_slug='PBS E 1', title='Essays, Letters from Abroad, Translations and Fragments', subtitle='',
               author_id='10', author_first_name='Percy Bysshe', author_last_name='Shelley',
               editor_translator='Mary Shelley', edition='1st', number_of_volumes='2', volume_number='1',
               publisher='Edward Moxon', place_of_pub='London', year_of_pub='1840', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b27 = Book(human_slug='PBS E 2', title='Essays, Letters from Abroad, Translations and Fragments', subtitle='',
               author_id='10', author_first_name='Percy Bysshe', author_last_name='Shelley',
               editor_translator='Mary Shelley', edition='1st', number_of_volumes='2', volume_number='2',
               publisher='Edward Moxon', place_of_pub='London', year_of_pub='1840', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b28 = Book(human_slug='PBS PP', title='Posthumous Poems', subtitle='', author_id='10',
               author_first_name='Percy Bysshe', author_last_name='Shelley', editor_translator='', edition='1st',
               number_of_volumes='', volume_number='', publisher='John and Henry L. Hunt', place_of_pub='London',
               year_of_pub='1824', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b29 = Book(human_slug='PBS PW 1', title='Poetical Works', subtitle='', author_id='10',
               author_first_name='Percy Bysshe', author_last_name='Shelley', editor_translator='Mary Shelley',
               edition='1st', number_of_volumes='2', volume_number='1', publisher='Edward Moxon', place_of_pub='London',
               year_of_pub='1839', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b30 = Book(human_slug='PBS PW 2', title='Poetical Works', subtitle='', author_id='10',
               author_first_name='Percy Bysshe', author_last_name='Shelley', editor_translator='Mary Shelley',
               edition='1st', number_of_volumes='2', volume_number='2', publisher='Edward Moxon', place_of_pub='London',
               year_of_pub='1839', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b31 = Book(human_slug='AT DA 1', title='De la Démocratie en Amérique', subtitle='', author_id='11',
               author_first_name='Alexis de', author_last_name='Tocqueville', editor_translator='', edition='2nd',
               number_of_volumes='4 vols.', volume_number='1', publisher='Librairie de Charles Gosselin',
               place_of_pub='Paris', year_of_pub='1835-40', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b32 = Book(human_slug='AT DA 2', title='De la Démocratie en Amérique', subtitle='', author_id='11',
               author_first_name='Alexis de', author_last_name='Tocqueville', editor_translator='', edition='2nd',
               number_of_volumes='4 vols.', volume_number='2', publisher='Librairie de Charles Gosselin',
               place_of_pub='Paris', year_of_pub='1835-40', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b33 = Book(human_slug='AT DA 3', title='De la Démocratie en Amérique', subtitle='', author_id='11',
               author_first_name='Alexis de', author_last_name='Tocqueville', editor_translator='', edition='2nd',
               number_of_volumes='4 vols.', volume_number='3', publisher='Librairie de Charles Gosselin',
               place_of_pub='Paris', year_of_pub='1835-40', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b34 = Book(human_slug='AT DA 3', title='De la Démocratie en Amérique', subtitle='', author_id='11',
               author_first_name='Alexis de', author_last_name='Tocqueville', editor_translator='', edition='2nd',
               number_of_volumes='4 vols.', volume_number='', publisher='Librairie de Charles Gosselin',
               place_of_pub='Paris', year_of_pub='1835-40', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b35 = Book(human_slug='AT DA 4', title='De la Démocratie en Amérique', subtitle='', author_id='11',
               author_first_name='Alexis de', author_last_name='Tocqueville', editor_translator='', edition='2nd',
               number_of_volumes='4 vols.', volume_number='4', publisher='Librairie de Charles Gosselin',
               place_of_pub='Paris', year_of_pub='1835-40', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b36 = Book(human_slug='AT OCI 1', title="Oeuvres et Correspondance Inédites d'Alexis de Tocqueville", subtitle='',
               author_id='11', author_first_name='Alexis de', author_last_name='Tocqueville',
               editor_translator='Gustave de Beaumont, ed.', edition='1st', number_of_volumes='2 vols.',
               volume_number='1', publisher='Michel Levy Freres', place_of_pub='Paris', year_of_pub='1861',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b37 = Book(human_slug='AT OCI 2', title="Oeuvres et Correspondance Inédites d'Alexis de Tocqueville", subtitle='',
               author_id='11', author_first_name='Alexis de', author_last_name='Tocqueville',
               editor_translator='Gustave de Beaumont, ed.', edition='1st', number_of_volumes='2 vols.',
               volume_number='2', publisher='Michel Levy Freres', place_of_pub='Paris', year_of_pub='1861',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b38 = Book(human_slug='AT ARR', title="L'Ancien Régime et la Révolution", subtitle='', author_id='11',
               author_first_name='Alexis de', author_last_name='Tocqueville', editor_translator='', edition='1st',
               number_of_volumes='', volume_number='', publisher='Michel Levy Freres', place_of_pub='Paris',
               year_of_pub='1856', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b39 = Book(human_slug='JSM DA', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b40 = Book(human_slug='JSM DA', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b41 = Book(human_slug='JSM B', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b42 = Book(human_slug='JSM B', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b43 = Book(human_slug='JSM W', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b44 = Book(human_slug='JSM W', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b45 = Book(human_slug='JSM M', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b46 = Book(human_slug='JSM M', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b47 = Book(human_slug='JSM HF', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b48 = Book(human_slug='JSM CQ', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b49 = Book(human_slug='JSM CL', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b50 = Book(human_slug='JSM CL', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b51 = Book(human_slug='JSM LPE', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b52 = Book(human_slug='JSM G', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b53 = Book(human_slug='JSM G', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b54 = Book(human_slug='JSM D', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b55 = Book(human_slug='JSM HG', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b56 = Book(human_slug='JSM FR', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b57 = Book(human_slug='JSM NQ', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b58 = Book(human_slug='JSM MP', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b59 = Book(human_slug='JSM PE', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b60 = Book(human_slug='JSM HG', title='J. S. M. 1840-1858', subtitle='', author_id='12',
               author_first_name='John Stuart', author_last_name='Mill', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='', place_of_pub='', year_of_pub='', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b61 = Book(human_slug='FB W 1', title='The Works', subtitle='Philosophical Works', author_id='13',
               author_first_name='Francis', author_last_name='Bacon',
               editor_translator='Editors: James Spedding, Robert Leslie Ellis, Douglas Denon Heath', edition='1st ',
               number_of_volumes='14', volume_number='1', publisher='Longman and Co. [plus others]',
               place_of_pub='London', year_of_pub='1857-1874', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b62 = Book(human_slug='FB W 2', title='The Works', subtitle='Philosophical Works', author_id='13',
               author_first_name='Francis', author_last_name='Bacon',
               editor_translator='Editors: James Spedding, Robert Leslie Ellis, Douglas Denon Heath', edition='1st ',
               number_of_volumes='14', volume_number='2', publisher='Longman and Co. [plus others]',
               place_of_pub='London', year_of_pub='1857-1874', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b63 = Book(human_slug='', title='The Works', subtitle='Philosophical Works', author_id='13',
               author_first_name='Francis', author_last_name='Bacon',
               editor_translator='Editors: James Spedding, Robert Leslie Ellis, Douglas Denon Heath', edition='1st',
               number_of_volumes='14', volume_number='5', publisher='Longman and Co. [plus others]',
               place_of_pub='London', year_of_pub='1857-1874', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b64 = Book(human_slug='FB W 6', title='The Works', subtitle='Literary and Professional Works', author_id='13',
               author_first_name='Francis', author_last_name='Bacon',
               editor_translator='Editors: James Spedding, Robert Leslie Ellis, Douglas Denon Heath', edition='1st',
               number_of_volumes='14', volume_number='6', publisher='Longman and Co. [plus others]',
               place_of_pub='London', year_of_pub='1857-1874', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b65 = Book(human_slug='FB W 7', title='The Works', subtitle='Literary and Professional Works', author_id='13',
               author_first_name='Francis', author_last_name='Bacon',
               editor_translator='Editors: James Spedding, Robert Leslie Ellis, Douglas Denon Heath', edition='1st',
               number_of_volumes='14', volume_number='7', publisher='Longman, Green and Co. [plus others]',
               place_of_pub='London', year_of_pub='1857-1874', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b66 = Book(human_slug='', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='8 (1)',
               publisher='Longman, Green, Longman and Roberts', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b67 = Book(human_slug='', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='9 (2)',
               publisher='Longman, Green, Longman and Roberts', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b68 = Book(human_slug='FB W 10', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='10 (3)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b69 = Book(human_slug='FB W 10', title='The Works ', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='10 (3)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b70 = Book(human_slug='FB W 11', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='11 (4)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b71 = Book(human_slug='FB W 12', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='12 (5)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b72 = Book(human_slug='FB W 12', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='12 (5)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1875',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b73 = Book(human_slug='FB W 13', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='13 (6)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b74 = Book(human_slug='FB W 12', title='The Works', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='Editor: James Spedding',
               edition='1st', number_of_volumes='14', volume_number='13 (6)',
               publisher='Longmans, Green, Reader and Dyer', place_of_pub='London', year_of_pub='1861-1874',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b75 = Book(human_slug='FB W 14', title='The Works ', subtitle='The Letters and The Life', author_id='13',
               author_first_name='Francis', author_last_name='Bacon',
               editor_translator='Editors: James Spedding, Robert Leslie Ellis, Douglas Denon Heath', edition='1st',
               number_of_volumes='14', volume_number='14 (7)', publisher='Longmans, Green, Reader and Dyer',
               place_of_pub='London', year_of_pub='1857-1874', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b76 = Book(human_slug='FB HRHSAR', title='Historia Regni Henrici Septimi Angliae Regis', subtitle='',
               author_id='13', author_first_name='Francis', author_last_name='Bacon', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='Officina Elzeviriana', place_of_pub='Amsterdam',
               year_of_pub='1662', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b77 = Book(human_slug='FB NOS', title='Novum Organum Scientarium', subtitle='', author_id='13',
               author_first_name='Francis', author_last_name='Bacon', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='Johann Ravestein', place_of_pub='Amsterdam',
               year_of_pub='1660', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b78 = Book(human_slug='FB SF', title='Sermones Fideles', subtitle='', author_id='13', author_first_name='Francis',
               author_last_name='Bacon', editor_translator='', edition='', number_of_volumes='', volume_number='',
               publisher='Franciscum Hackium [Francis Hack?]', place_of_pub='', year_of_pub='1644', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b79 = Book(human_slug='AB SI', title='The Senses and The Intellect', subtitle='', author_id='14',
               author_first_name='Alexander', author_last_name='Bain', editor_translator='', edition='3rd',
               number_of_volumes='', volume_number='', publisher='Longmans, Green and Co.', place_of_pub='London',
               year_of_pub='1868', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b80 = Book(human_slug='TSB NVC', title='A New View of Causation', subtitle='', author_id='15',
               author_first_name='Thomas Squire', author_last_name='Barrett', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='Provost & Co.', place_of_pub='London',
               year_of_pub='1871', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b81 = Book(human_slug='PB SP', title='Systeme de Philosophie…', subtitle='', author_id='16',
               author_first_name='Pierre', author_last_name='Bayle', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='Samuel Pitra, Libraire Du Roi', place_of_pub='Berlin',
               year_of_pub='1785', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b82 = Book(human_slug='TSB ENALF', title='An Essay on the New Analytic of Logical Forms', subtitle='',
               author_id='17', author_first_name='Thomas Spencer', author_last_name='Baynes', editor_translator='',
               edition='', number_of_volumes='', volume_number='',
               publisher='Sutherland and Knox; Simpkin, Marshall and Co.', place_of_pub='Edinburgh; London',
               year_of_pub='1850', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b83 = Book(human_slug='TSB ENEALF', title='An Essay on the New Analytic of Logical Forms', subtitle='',
               author_id='17', author_first_name='Thomas Spencer', author_last_name='Baynes', editor_translator='',
               edition='', number_of_volumes='', volume_number='',
               publisher='Sutherland and Knox; Simpkin, Marshall and Co.', place_of_pub='Edinburgh; London',
               year_of_pub='1850', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b84 = Book(human_slug='JB DMC', title='Dissertations Moral and Critical', subtitle='', author_id='18',
               author_first_name='James', author_last_name='Beattie', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='W Strahan and T Cadell; W. Creech',
               place_of_pub='London; Edinburgh', year_of_pub='1783', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b85 = Book(human_slug='JB EMS 1', title='Elements of Moral Science', subtitle='', author_id='18',
               author_first_name='James', author_last_name='Beattie', editor_translator='', edition='',
               number_of_volumes='2', volume_number='1', publisher='William Creech; T Cadell',
               place_of_pub='Edinburgh; London', year_of_pub='1790-1793', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b86 = Book(human_slug='JB EMS 2', title='Elements of Moral Science', subtitle='', author_id='18',
               author_first_name='James', author_last_name='Beattie', editor_translator='', edition='',
               number_of_volumes='2', volume_number='2', publisher='William Creech; T Cadell',
               place_of_pub='Edinburgh; London', year_of_pub='1790-1793', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b87 = Book(human_slug='JB EMS 2', title='The Works ', subtitle='', author_id='19', author_first_name='George',
               author_last_name='Berkeley', editor_translator='', edition='', number_of_volumes='3', volume_number='2',
               publisher='Richard Priestley', place_of_pub='London', year_of_pub='1820', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b88 = Book(human_slug='JB EMS 3', title='The Works ', subtitle='', author_id='19', author_first_name='George',
               author_last_name='Berkeley', editor_translator='', edition='', number_of_volumes='3', volume_number='3',
               publisher='Richard Priestley', place_of_pub='London', year_of_pub='1820', spine_image='!!!',
               full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b89 = Book(human_slug='FB TL', title='A Treatise on Logic, or, The Laws of Pure Thought', subtitle='',
               author_id='20', author_first_name='Francis', author_last_name='Bowen', editor_translator='',
               edition='1st', number_of_volumes='', volume_number='', publisher='Sever and Francis',
               place_of_pub='Cambridge', year_of_pub='1864', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b90 = Book(human_slug='JB EC', title='Essays on the Characteristics', subtitle='', author_id='21',
               author_first_name='John', author_last_name='Brown', editor_translator='', edition='3rd',
               number_of_volumes='', volume_number='', publisher='C. Davis', place_of_pub='London', year_of_pub='1752',
               spine_image='!!!', full_text_edition_link='', period_translation_link='', raw_import='!!!')
    b91 = Book(human_slug='TB IRCE', title='Inquiry into the Relation of Cause and Effect', subtitle='', author_id='22',
               author_first_name='Thomas', author_last_name='Brown', editor_translator='', edition='3rd',
               number_of_volumes='', volume_number='', publisher='Archibald Constable and Co.',
               place_of_pub='Edinburgh', year_of_pub='1818', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b92 = Book(human_slug='JB IHP', title='Institutiones Historiae Philosophicae…', subtitle='', author_id='23',
               author_first_name='Jacob', author_last_name='Brucker', editor_translator='', edition='3rd',
               number_of_volumes='', volume_number='', publisher='Joh. Gottlob Immanuel Breitkopfii',
               place_of_pub='Lipsiae [Leipzig]', year_of_pub='1790', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b93 = Book(human_slug='FB IL 1', title='Institutionum Logicarum Libri Duo', subtitle='', author_id='24',
               author_first_name='Fr.', author_last_name='Burgersdicius', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='John Field', place_of_pub='Cambridge',
               year_of_pub='1660', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b94 = Book(human_slug='FB IL', title='Institutionum Logicarum Libri Duo', subtitle='', author_id='24',
               author_first_name='Fr.', author_last_name='Burgersdicius', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='John Field', place_of_pub='Cambridge',
               year_of_pub='1660', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b95 = Book(human_slug='FB IL 2', title='Institutionum Logicarum Libri Duo', subtitle='', author_id='24',
               author_first_name='Fr.', author_last_name='Burgersdicius', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='John Field', place_of_pub='Cambridge',
               year_of_pub='1660', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b96 = Book(human_slug='FB IL 2', title='Institutionum Logicarum Libri Duo', subtitle='', author_id='24',
               author_first_name='Fr.', author_last_name='Burgersdicius', editor_translator='', edition='',
               number_of_volumes='', volume_number='', publisher='John Field', place_of_pub='Cambridge',
               year_of_pub='1661', spine_image='!!!', full_text_edition_link='', period_translation_link='',
               raw_import='!!!')
    b97 = Book(human_slug='EB PESB', title='A Philosophical Enquiry into...the Sublime and Beautiful', subtitle='',
               author_id='25', author_first_name='Edmund', author_last_name='Burke', editor_translator='',
               edition='1st', number_of_volumes='', volume_number='', publisher='R and J. Dodsley',
               place_of_pub='London', year_of_pub='1757', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')
    b98 = Book(human_slug='', title='A Philosophical Enquiry into...the Sublime and Beautiful', subtitle='',
               author_id='25', author_first_name='Edmund', author_last_name='Burke', editor_translator='',
               edition='1st', number_of_volumes='', volume_number='', publisher='R and J. Dodsley',
               place_of_pub='London', year_of_pub='1757', spine_image='!!!', full_text_edition_link='',
               period_translation_link='', raw_import='!!!')

    db.session.add(b1)
    db.session.add(b2)
    db.session.add(b3)
    db.session.add(b4)
    db.session.add(b5)
    db.session.add(b6)
    db.session.add(b7)
    db.session.add(b8)
    db.session.add(b9)
    db.session.add(b10)
    db.session.add(b11)
    db.session.add(b12)
    db.session.add(b13)
    db.session.add(b14)
    db.session.add(b15)
    db.session.add(b16)
    db.session.add(b17)
    db.session.add(b18)
    db.session.add(b19)
    db.session.add(b20)
    db.session.add(b21)
    db.session.add(b22)
    db.session.add(b23)
    db.session.add(b24)
    db.session.add(b25)
    db.session.add(b26)
    db.session.add(b27)
    db.session.add(b28)
    db.session.add(b29)
    db.session.add(b30)
    db.session.add(b31)
    db.session.add(b32)
    db.session.add(b33)
    db.session.add(b34)
    db.session.add(b35)
    db.session.add(b36)
    db.session.add(b37)
    db.session.add(b38)
    db.session.add(b39)
    db.session.add(b40)
    db.session.add(b41)
    db.session.add(b42)
    db.session.add(b43)
    db.session.add(b44)
    db.session.add(b45)
    db.session.add(b46)
    db.session.add(b47)
    db.session.add(b48)
    db.session.add(b49)
    db.session.add(b50)
    db.session.add(b51)
    db.session.add(b52)
    db.session.add(b53)
    db.session.add(b54)
    db.session.add(b55)
    db.session.add(b56)
    db.session.add(b57)
    db.session.add(b58)
    db.session.add(b59)
    db.session.add(b60)
    db.session.add(b61)
    db.session.add(b62)
    db.session.add(b63)
    db.session.add(b64)
    db.session.add(b65)
    db.session.add(b66)
    db.session.add(b67)
    db.session.add(b68)
    db.session.add(b69)
    db.session.add(b70)
    db.session.add(b71)
    db.session.add(b72)
    db.session.add(b73)
    db.session.add(b74)
    db.session.add(b75)
    db.session.add(b76)
    db.session.add(b77)
    db.session.add(b78)
    db.session.add(b79)
    db.session.add(b80)
    db.session.add(b81)
    db.session.add(b82)
    db.session.add(b83)
    db.session.add(b84)
    db.session.add(b85)
    db.session.add(b86)
    db.session.add(b87)
    db.session.add(b88)
    db.session.add(b89)
    db.session.add(b90)
    db.session.add(b91)
    db.session.add(b92)
    db.session.add(b93)
    db.session.add(b94)
    db.session.add(b95)
    db.session.add(b96)
    db.session.add(b97)
    db.session.add(b98)
    db.session.commit()
    return "Import Complete"

