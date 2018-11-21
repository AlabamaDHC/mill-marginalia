import sqlalchemy
from flask import render_template, request, flash, redirect, url_for, jsonify, json, Response
from flask_security import login_required

# import importData
from app import app, db
# from models import User, Role, Book, Page, Marginalia, Author, ImportItem
from constants import *
import re

from difflib import SequenceMatcher

from models.author import Author
from models.book import Book
from models.page import Page
from models.marginalia import Marginalia
from models.import_models import ImportItem



@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/marginalia')
@login_required
def admin_marginalia():
    marginalia = Marginalia.query.all()
    return render_template('admin/table-pages.html', marginalia=marginalia)

@app.route('/admin/marginalia/<marg_id>', methods=['GET', 'POST'])
@login_required
def admin_marginalia_form(marg_id):
    return ""

@app.route('/admin/pages')
@login_required
def admin_pages():
    pages = Page.query.all()
    return render_template('admin/table-pages.html', pages=pages)

@app.route('/admin/pages/<page_id>', methods=['GET', 'POST'])
@login_required
def admin_page_form(page_id):
    page = Page.query.filter_by(id=page_id).first()
    if request.method == 'GET':
        return render_template('admin/form-page.html', page=page)
    if request.method == 'POST':
        form = request.form

        if 'title' in request.form:
            form_val = request.form['title']
            page.title = request.form['title']

        if 'subtitle' in request.form:
            form_val = request.form['subtitle']
            page.subtitle = request.form['subtitle']

        db.session.commit()

        flash('Changes saved successfully')
        return redirect(url_for('admin_page_form', page_id=page_id))


@app.route('/admin/books')
@login_required
def admin_books():
    books = Book.query.all()
    return render_template('admin/table-books.html', books=books)


@app.route('/admin/books/<book_id>', methods=['GET', 'POST'])
@login_required
def admin_book_form(book_id):
    # book = Book.query.filter_by(slug=book_slug).first()
    book = db.session.query(Book).get(book_id)
    # book = Book.query.get_or_404(book_id)

    if request.method == 'GET':
        return render_template('admin/form-book.html', book=book)
    if request.method == 'POST':
        form = request.form

        if 'title' in request.form:
            form_val = request.form['title']
            book.title = request.form['title']

        if 'subtitle' in request.form:
            form_val = request.form['subtitle']
            book.subtitle = request.form['subtitle']

        if 'author_first_name' in request.form:
            form_val = request.form['author_first_name']
            book.author_first_name = request.form['author_first_name']

        if 'author_last_name' in request.form:
            form_val = request.form['author_last_name']
            book.author_last_name = request.form['author_last_name']

        if 'editor_translator' in request.form:
            form_val = request.form['editor_translator']
            book.editor_translator = request.form['editor_translator']

        if 'edition' in request.form:
            form_val = request.form['edition']
            book.edition = request.form['edition']

        if 'number_of_volumes' in request.form:
            form_val = request.form['number_of_volumes']
            book.number_of_volumes = request.form['number_of_volumes']

        if 'volume_number' in request.form:
            form_val = request.form['volume_number']
            book.volume_number = request.form['volume_number']

        if 'publisher' in request.form:
            form_val = request.form['publisher']
            book.publisher = request.form['publisher']

        if 'place_of_pub' in request.form:
            form_val = request.form['place_of_pub']
            book.place_of_pub = request.form['place_of_pub']

        if 'year_of_pub' in request.form:
            form_val = request.form['year_of_pub']
            book.year_of_pub = request.form['year_of_pub']

        if 'full_text_edition_link' in request.form:
            form_val = request.form['full_text_edition_link']
            book.full_text_edition_link = request.form['full_text_edition_link']

        if 'period_translation_link' in request.form:
            form_val = request.form['period_translation_link']
            book.period_translation_link = request.form['period_translation_link']

        if 'public' in request.form:
            form_val = request.form['public']
            book.public = request.form['public']

        if 'notes' in request.form:
            form_val = request.form['notes']
            book.notes = request.form['notes']

        db.session.commit()

        flash('Changes saved successfully')
        return redirect(url_for('admin_book_form', book_id=book_id))



@app.route('/admin/import/run_error_checks')
@login_required
def admin_run_error_checks():
    sheet = request.args.get('sheet', '')
    error_only = request.args.get('errorsonly', '')

    if sheet and not sheet == 'all':
        if error_only:
            query = db.session.query(ImportItem).filter(ImportItem.error_text.isnot(None))

        else:
            query = db.session.query(ImportItem).filter(ImportItem.sheet_name == sheet)

        for item in query:
            item.run_error_checks()

    else:
        if error_only:
            query = db.session.query(ImportItem).filter(ImportItem.error_text.isnot(None))

        else:
            query = db.session.query(ImportItem).all()

        for item in query:
            item.run_error_checks()

    # return "Success"
    return redirect(url_for('admin_failed_imports')+'?sheet='+sheet)

@app.route('/admin/import/run_import')
@login_required
def admin_run_import():
    # i = ImportItem.query.get_or_404(import_id)
    sheet = request.args.get('sheet', '')
    error_only = request.args.get('errorsonly', '')

    if sheet and not sheet == 'all':
        if error_only:
            query = db.session.query(ImportItem).filter(ImportItem.sheet_name == sheet, ImportItem.error_text == None)

        else:
            query = db.session.query(ImportItem).filter(ImportItem.sheet_name == sheet)

    else:
        if error_only:
            query = db.session.query(ImportItem).filter(ImportItem.error_text == None)

        else:
            query = db.session.query(ImportItem).all()

    for item in query:
        item.run_import()
    return 'Success'





# class ImportItem():
#     def __init__(self, sheet_name, row, import_row, raw_row):
#         self.sheet_name = sheet_name
#         self.row = row
#         self.author_last_name = import_row[0]
#         self.author_first_name = import_row[1]
#         self.title = import_row[2]
#         self.subtitle = import_row[3]
#         self.editor_translator = import_row[4]
#         self.number_of_volumes = import_row[5]
#         self.edition = import_row[6]
#         self.place_of_pub = import_row[7]
#         self.publisher = import_row[8]
#         self.year_of_pub = import_row[9]
#         self.volume_number = import_row[10]
#         self.part_of_book = import_row[12]
#         self.location_in_book = import_row[11]
#         self.page_image = import_row[13].rstrip()
#         self.close_image = import_row[14]
#         self.page_num = import_row[15]
#         self.location_on_page = import_row[16]
#         self.writing_implement = import_row[18]
#         self.line_number = import_row[17]
#         self.type = import_row[19]
#         self.subtype = import_row[20]
#         self.language = import_row[21]
#         self.transcription = import_row[22]
#         self.imported = False
#         self.raw_row = raw_row
#         self.error_log = list()
#
#         self.book = None
#         self.author = None
#         self.page = None
#
#         self.human_slug = self.page_image.split(".")[0]
#         self.slug = self.human_slug.replace(' ', '-')
#
#         self.check_page_image()
#         self.check_volume_fields()
#
#         if self.location_in_book == 'title page' or self.location_in_book == 'title':
#             self.page_num = 'title page'
#             self.page_order = 10
#
#     def run_import(self):
#         if len(self.error_log) > 0:
#             if not self.check_author_exists():
#                 self.add_author()
#
#             if not self.check_book_exists():
#                 self.add_book()
#
#             if not self.check_page_exists():
#                 self.add_page()
#             self.imported = False
#         else:
#             self.imported = True
#
#
#     def check_author_exists(self):
#         self.author = Author.query.filter_by(last_name=self.author_last_name).filter_by(first_name=self.author_first_name).first()
#         if self.author != None:
#             True
#         else:
#             False
#
#     def check_book_exists(self):
#         self.book = Book.query.filter_by(slug=self.slug).first()
#         if self.book != None:
#             True
#         else:
#             False
#
#     def check_page_exists(self):
#         self.page = Page.query.filter_by(book_id=self.book.id, page_image=self.page_image).first()
#         if self.page != None:
#             True
#         else:
#             False
#         pass
#
#     def add_author(self):
#         author = Author(first_name=self.author_first_name, last_name=self.author_last_name, image='', image_caption='')
#         db.session.add(author)
#         db.session.commit()
#
#     def add_book(self):
#         book = Book(human_slug=self.human_slug,
#                     title=self.title, subtitle=self.subtitle, author_id=self.author.id,
#                     author_first_name=self.author_first_name, author_last_name=self.author_last_name,
#                     editor_translator=self.editor_translator, edition=self.edition,
#                     number_of_volumes=self.number_of_volumes, volume_number=self.volume_number, part_of_book=self.part_of_book,
#                     publisher=self.publisher, place_of_pub=self.place_of_pub, year_of_pub=self.year_of_pub,
#                     full_text_edition_link='', period_translation_link='',
#                     spine_image='',
#                     raw_import=self.raw_row)
#
#     def add_page(self):
#         last_page = Page.query.filter_by(book_id=self.book.id).order_by(sqlalchemy.desc(Page.id)).first()
#         if last_page != None:
#             page = Page(page_num=self.page_num, book_id=self.book.id,
#                         location_in_book=self.location_in_book, page_image=self.page_image, page_order=last_page.page_order + 10)
#         else:
#             page = Page(page_num=self.page_num, book_id=self.book.id,
#                         location_in_book=self.location_in_book, page_image=self.page_image, page_order=10)
#         db.session.add(page)
#         db.session.commit()
#
#
#     def check_page_image(self):
#         if (self.page_image == "" or self.page_image == " "):
#             self.error_log.append('ROW {0}: Slug/Page Image field blank at index. Skipping row'.format(self.row))
#
#
#
#     def check_volume_fields(self):
#         if self.volume_number == '':
#             self.volume_number = 1
#
#         try:
#             self.volume_number = int(self.volume_number)
#
#         except ValueError as verr:
#             self.error_log.append('ROW {0}: volume_number not a valid number'.format(self.row))  # do job to handle: s does not contain anything convertible to int
#
#         except Exception as ex:
#             pass
#             self.error_log.append('ROW {0}: volume_number not a valid number'.format(self.row))
#
#         if self.number_of_volumes == '':
#             self.number_of_volumes = 1
#
#         try:
#             self.number_of_volumes = int(self.number_of_volumes)
#
#         except ValueError as verr:
#             self.error_log.append('ROW {0}: number_of_volumes not a valid number'.format(
#                 self.row))  # do job to handle: s does not contain anything convertible to int
#
#         except Exception as ex:
#             pass
#             self.error_log.append('ROW {0}: number_of_volumes not a valid number'.format(self.row))
#
#



@app.route('/admin/import/failedimports', methods=['GET', 'POST'])
@login_required
def admin_failed_imports():

    if request.method == 'GET':
        sheet = request.args.get('sheet', '')

        # imported_sheets = [{'name': 'All', 'count': str(db.session.query(ImportItem.row).count())}]
        imported_sheets = []
        imported_sheets_query = db.session.query(ImportItem.sheet_name).distinct(ImportItem.sheet_name)

        count = 0
        for i in imported_sheets_query:
            q = db.session.query(ImportItem.id).filter(ImportItem.sheet_name == i.sheet_name, ImportItem.error_text.isnot(None)).count()
            count += q
            imported_sheets.append(
                {'name': i.sheet_name, 'count': str(q)}
            )

        imported_sheets.insert(0,
            {'name': 'All', 'count': count}
        )


        if sheet:
            if sheet == 'all':
                failed = db.session.query(ImportItem).filter(ImportItem.error_text.isnot(None))
                return render_template('admin/failed-imports.html', active=sheet, imported_sheets=imported_sheets,
                                       failed=failed)
            else:
                failed = db.session.query(ImportItem).filter(ImportItem.sheet_name == sheet, ImportItem.error_text.isnot(None))
                return render_template('admin/failed-imports.html', active=sheet, imported_sheets=imported_sheets, failed=failed)

        else:
            failed = db.session.query(ImportItem).filter(ImportItem.error_text.isnot(None))
        return render_template('admin/failed-imports.html', active=sheet, imported_sheets=imported_sheets, failed=failed)



@app.route('/admin/import', methods=['GET', 'POST'])
@login_required
def admin_import():
    if request.method == 'GET':
        return render_template('admin/import.html', book_map=default_book_import_mapping)

    if request.method == 'POST':
        if 'import_from_spreadsheet' in request.form and request.form['import_from_spreadsheet'] is not '':
            spreadsheet_name = request.form['spreadsheet_name']
            form_val = request.form['import_from_spreadsheet']
            list = form_val.split('\r\n')
            # b = list[0].split('\t')

            index = 2

            for item in list:
                if 'Author Last Name' in item: #skip column label row if included
                    continue

                i = ImportItem(sheet_name=spreadsheet_name, row=index, import_row=item.split('\t'), raw_row=item)

                # i_dup = ImportItem.query.filter_by(sheet_name=spreadsheet_name).filter_by(row=index).first()
                i_dup = db.session.query(ImportItem.sheet_name, ImportItem.row, ImportItem.raw_row).filter(ImportItem.sheet_name == spreadsheet_name, ImportItem.row == index).first()

                if i_dup and i_dup.raw_row == i.raw_row:
                    continue

                db.session.add(i)
                db.session.commit()
                index += 1

        return redirect(url_for('admin_failed_imports'))





@app.route('/admin/import_OLD', methods=['GET', 'POST'])
@login_required
def admin_import_OLD():
    if request.method == 'GET':
        return render_template('admin/import-OLD.html', book_map=default_book_import_mapping)
    if request.method == 'POST':
        form = request.form

        if 'import_books' in request.form and request.form['import_books'] is not '':
            form_val = request.form['import_books']
            list = form_val.split('\r\n')
            b = list[0].split('\t')

            for item in list:
                raw_item = item
                item = item.split('\t')
                import_map = old_book_import_mapping
                b = Book(human_slug=item[import_map['human_slug_map_col']],
                         title=item[import_map['title_map_col']],
                         subtitle=item[import_map['subtitle_map_col']],
                         author_first_name=item[import_map['author_first_name_map_col']],
                         author_last_name=item[import_map['author_last_name_map_col']],
                         editor_translator=item[import_map['editor_translator_map_col']],
                         edition=item[import_map['edition_map_col']],
                         number_of_volumes=item[import_map['number_of_volumes_map_col']],
                         volume_number=item[import_map['volume_number_map_col']],
                         publisher=item[import_map['publisher_map_col']],
                         place_of_pub=item[import_map['place_of_pub_map_col']],
                         year_of_pub=item[import_map['year_of_pub_map_col']],
                         full_text_edition_link=item[import_map['full_text_edition_link_map_col']],
                         period_translation_link=item[import_map['period_translation_link_map_col']],
                         spine_image=item[import_map['spine_image_map_col']],
                         raw_import=raw_item)
                db.session.add(b)
                db.session.commit()
                flash_message = 'Imported ' + b.title
                # flash_message = 'Imported ' + b.title + '<a style="color: #337ab7;" href="/admin/book/' + b.id + '">\tView</a>'
                flash(flash_message, 'alert-success')


        if 'import_from_spreadsheet' in request.form and request.form['import_from_spreadsheet'] is not '':
            form_val = request.form['import_from_spreadsheet']
            list = form_val.split('\r\n')
            b = list[0].split('\t')

            # author_log = []
            # book_log = []
            # page_log = []
            # marg_log = []
            log = []
            error_log = []

            index = 1
            prev_item = None

            for item in list:
                index += 1
                raw_item = item
                item = item.split('\t')

                if len(item) < 25:
                    item += [''] * (25 - len(item))

                location_in_book = item[11]
                page_image = item[13]

                if location_in_book == 'spine':
                    error_log.append('ROW {0}: Spine record. Skipping row'.format(index))
                    continue

                if(page_image == "" or page_image == " "):
                    error_log.append('ROW {0}: Slug/Page Image field blank at index. Skipping row'.format(index))
                    log.append('Slug/Page Image field blank at index {0}. Skipping row'.format(index))
                    continue

                title = item[2]
                subtitle = item[3]
                author_first_name = item[1]
                author_last_name = item[0]

                if (item[1] == "" or item[1] == " " or item[0] == "" or item[0] == " "):
                    error_log.append('ROW {0}: Author fields blank at index. Skipping row'.format(index))
                    log.append('Author fields blank at index {0}. Skipping row'.format(index))
                    continue

                author = Author.query.filter_by(last_name=author_last_name).filter_by(first_name=author_first_name).first()
                if author != None:
                    log.append('Author <ID: {0}> {1} {2} already exists'.format(author.id, author.first_name, author.last_name))
                else:
                    author = Author(first_name=author_first_name, last_name=author_last_name, image='', image_caption='')
                    log.append('Author <ID: {0}> {1} {2} created'.format(author.id, author.first_name, author.last_name))
                    db.session.add(author)
                    db.session.commit()


                editor_translator = item[4]
                edition = item[6]

                volume_number = item[10]
                number_of_volumes = item[5]
                if volume_number == '':
                    volume_number = 1

                if number_of_volumes == '':
                    number_of_volumes = 1

                try:
                    volume_number = int(volume_number)
                    number_of_volumes = int(number_of_volumes)
                except ValueError as verr:
                    error_log.append('ROW {0}: volume_number OR number_of_volumes not a valid number'.format(index))  # do job to handle: s does not contain anything convertible to int
                except Exception as ex:
                    error_log.append('ROW {0}: volume_number OR number_of_volumes not a valid number'.format(index))  # do job to handle: Exception occurred while converting to int


                # number_of_volumes = re.sub('[^0-9]', '', item[5])  # strip non-numerical numbers
                # volume_number = re.sub('[^0-9]', '', item[10])  # strip non-numerical numbers
                publisher = item[8]
                place_of_pub = item[7]
                year_of_pub = item[9]


                location_in_book = item[11]
                part_of_book = item[12]
                page_image = item[13].rstrip()
                page_num = item[15]

                close_image = item[14]
                location_on_page = item[16]
                writing_implement = item[18]
                line_number = item[17]
                type = item[19]
                subtype = item[20]
                language = item[21]

                transcription = item[22]
                hand = item[23]
                notes = ''
                if len(item) < 25:
                    notes = ''

                if len(item) < 11:
                    location_in_book = ''


                slug_split = page_image.split(".")
                human_slug = slug_split[0]
                slug = human_slug.replace(' ', '-')

                if prev_item:
                    human_slug_match = SequenceMatcher(None, human_slug, item[13].rstrip().split(".")[0]).ratio()
                    title_match = SequenceMatcher(None, title, prev_item[2]).ratio()
                    subtitle_match = SequenceMatcher(None, subtitle, prev_item[3]).ratio()
                    author_first_match = SequenceMatcher(None, author_first_name, prev_item[1]).ratio()
                    author_last_match = SequenceMatcher(None, author_last_name, prev_item[0]).ratio()

                    if human_slug_match < 1.0 and human_slug_match > 0.8:
                        print('ROW '+index+'human_slug_match: '+SequenceMatcher(None, human_slug, item[13].rstrip().split(".")[0]).ratio())

                    # if title_match < 1.0 and title_match > 0.8:
                    #     print(SequenceMatcher(None, title, prev_item[2]).ratio())
                    #
                    # if subtitle_match < 1.0 and subtitle_match > 0.8:
                    #     print(SequenceMatcher(None, title, prev_item[2]).ratio())
                    #
                    # if author_first_match < 1.0 and author_last_match > 0.8:
                    #     print(SequenceMatcher(None, title, prev_item[2]).ratio())
                    #
                    # if author_last_match < 1.0 and author_last_match > 0.8:
                    #     print(SequenceMatcher(None, title, prev_item[2]).ratio())

                book = Book.query.filter_by(slug=slug).first()
                if book != None:
                    log.append('Book <ID: {0}> {1} {2} {3} already exists'.format(book.id, book.title, book.subtitle, book.volume_number))
                else:
                    book = Book(human_slug=human_slug,
                             title=title, subtitle=subtitle, author_id=author.id,
                             author_first_name=author_first_name, author_last_name=author_last_name,
                             editor_translator=editor_translator, edition=edition,
                             number_of_volumes=number_of_volumes, volume_number=volume_number, part_of_book=part_of_book,
                             publisher=publisher, place_of_pub=place_of_pub, year_of_pub=year_of_pub,
                             full_text_edition_link='', period_translation_link='',
                             spine_image='',
                             raw_import=raw_item)
                    log.append('Book <ID: {0}> {1} {2} {3} created'.format(book.id, book.title, book.subtitle, book.volume_number))
                    db.session.add(book)
                    db.session.commit()

                if location_in_book == 'title page' or location_in_book == 'title':
                    page_num = 'title page'
                    page_order = 10

                page = Page.query.filter_by(book_id=book.id, page_image=page_image).first()
                if page != None:
                    log.append('Page <ID: {0}> exists'.format(page.id))
                else:
                    last_page = Page.query.filter_by(book_id=book.id).order_by(sqlalchemy.desc(Page.id)).first()
                    if last_page != None:
                        page = Page(page_num=page_num, book_id=book.id,
                                    location_in_book=location_in_book, page_image=page_image, page_order=last_page.page_order+10)
                    else:
                        page = Page(page_num=page_num, book_id=book.id,
                                location_in_book=location_in_book, page_image=page_image, page_order=10)
                        log.append('Page <ID: {0}> created'.format(page.id))
                    db.session.add(page)
                    db.session.commit()


                marg = Marginalia(page_id=page.id, book_id=book.id,
                                  location_on_page=location_on_page, line_number=line_number,
                                  writing_implement=writing_implement, type=type, subtype=subtype,
                                  language=language, transcription=transcription,
                                  close_image=close_image, notes=notes, hand=hand, raw_import=raw_item)
                db.session.add(marg)

                log.append('Marginalia <ID: {0}> created'.format(marg.id))

                db.session.commit()

                if index > 2:
                    prev_item = item


                # human_slug = item[]
                # full_text_edition_link = item[]
                # period_translation_link = item[]
                # spine_image = item[]
                # raw_import = raw_item


        if 'import_marginalia' in request.form and request.form['import_books'] is not '':
            form_val = request.form['import_marginalia']

    # flash('Changes saved successfully')
    # print(*log, sep="\n")
    print(*error_log, sep="\n")

    return redirect(url_for('admin_import'))


@app.route('/admin/users')
@login_required
def admin_users():
    users = User.query.all()
    return render_template('admin/table-users.html', users=users)



# @app.route('/load_books')
# @login_required
# def load_books():
#     importData.load_books()
#     return 'Loaded Books!'