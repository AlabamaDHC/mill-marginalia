from flask import render_template, request, flash, redirect, url_for, jsonify, json

# import importData
from sqlalchemy import cast, VARCHAR
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

@app.route('/api/')
def api_top():
    response = {
        'warning': 'The public API is currently in alpha. Changes will be made frequently and without notice. Somethings will probably get broken.',
        'routes':
            {
                'Authors': '/api/authors',
                'Volumes': '/api/volumes',
                'Book': '/api/book/<book_id>',
                'Metadata (Non-JSON)': '/api/metadata/<list:slugs>'

            }

    }
    return jsonify(response)



@app.route('/api/metadata/<list:slugs>')
def api_metadata(slugs):
    if len(slugs) > 20:
        return 'No more than 20 volumes may be queried at one time.'
    book_ids = []
    for slug in slugs:
        id_query = db.session.query(Book.id).filter_by(slug=slug).first_or_404()
        if id_query:
            book_ids.append(id_query.id)

    query = db.session.query(Marginalia).filter(Marginalia.book_id.in_((book_ids)))
    return render_template('front/metadata.html', metadata=query)



@app.route('/api/volumes/<book_id>')
def api_select_volume(book_id):
    # book = Book.query.filter_by(slug=book_slug).first_or_404()
    volume = Book.query.filter_by(id=book_id).first_or_404()

    volume_json = {
        'title': volume.title,
        'subtitle': volume.subtitle,
        'author': {
            'first_name': volume.author_first_name,
            'last_name': volume.author_last_name,
            'id': volume.author.id,
            'url': '/api/authors/' + volume.author.id
        },
        'edition': volume.edition,
        'number_of_volumes': volume.number_of_volumes,
        'publisher': volume.publisher,
        'place_of_pub': volume.place_of_pub,
        'year_of_pub': volume.year_of_pub,
        'full_text_edition_link': volume.full_text_edition_link,
        'period_translation_link': volume.period_translation_link,
        'critical_intro': volume.critical_intro,
        'slug_set': volume.slug,
        'volumes': []
    }


    return jsonify(p_list)


@app.route('/api/volumes/<book_id>/pages')
def api_book_pages(book_id):
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


@app.route('/api/authors')
def api_authors():

    query = Author.query.filter_by(public=True)
    # query = Author.query.filter_by(public=True).order_by(Author.last_name)

    meta = {
        # 'limit': int_limit,
        # 'offset': int_offset,
        'total': Author.query.count()
    }

    author_json = []
    for a in query:

        books = dict()

        for b in a.books:
            if b.spine_image[:-4] in books:
                books[b.spine_image[:-4]]['volumes'].append(
                    {
                        'title': b.title,
                        'subtitle': b.subtitle,
                        'edition': b.edition,
                        'volume_number': b.volume_number,
                        'part_of_book': b.part_of_book,
                        'url': url_for('show_book', book_slug=b.slug),
                        'id': b.id,
                        'spine': b.spine_image,
                    }

                )
                books[b.spine_image[:-4]]['slug_set'] = books[b.spine_image[:-4]]['slug_set']+'+'+b.slug

            else:
                books[b.spine_image[:-4]] = {
                        'spine': b.spine_image,
                        'number_of_volumes': b.number_of_volumes,
                        'slug_set': b.slug,
                        'volumes': [
                            {
                                'title': b.title,
                                'subtitle': b.subtitle,
                                'edition': b.edition,
                                'volume_number': b.volume_number,
                                'part_of_book': b.part_of_book,
                                'url': url_for('show_book', book_slug=b.slug),
                                'id': b.id,
                            }
                        ]
                    }

        author_json.append(
            {
                'first_name': a.first_name,
                'last_name': a.last_name,
                'image': a.image,
                'books': books,
                'id': a.id,
            }
        )

    response = {'meta': meta, 'data': author_json}
    return jsonify(response)


@app.route('/api/authors/<author_id>')
def api_single_author(author_id):

    query = Author.query.filter_by(id=author_id, public=True)
    # query = Author.query.filter_by(public=True).order_by(Author.last_name)

    meta = {
        # 'limit': int_limit,
        # 'offset': int_offset,
        'total': Author.query.count()
    }

    author_json = []
    for a in query:

        books = dict()

        for b in a.books:
            if b.spine_image[:-4] in books:
                books[b.spine_image[:-4]]['volumes'].append(
                    {
                        'title': b.title,
                        'subtitle': b.subtitle,
                        'edition': b.edition,
                        'volume_number': b.volume_number,
                        'part_of_book': b.part_of_book,
                        'url': url_for('show_book', book_slug=b.slug),
                        'id': b.id,
                        'spine': b.spine_image,
                    }

                )
                books[b.spine_image[:-4]]['slug_set'] = books[b.spine_image[:-4]]['slug_set']+'+'+b.slug

            else:
                books[b.spine_image[:-4]] = {
                        'spine': b.spine_image,
                        'number_of_volumes': b.number_of_volumes,
                        'slug_set': b.slug,
                        'volumes': [
                            {
                                'title': b.title,
                                'subtitle': b.subtitle,
                                'edition': b.edition,
                                'volume_number': b.volume_number,
                                'part_of_book': b.part_of_book,
                                'url': url_for('show_book', book_slug=b.slug),
                                'id': b.id,
                            }
                        ]
                    }

        author_json.append(
            {
                'first_name': a.first_name,
                'last_name': a.last_name,
                'image': a.image,
                'image_caption': a.image_caption,
                'books': books,
                'id': a.id,
            }
        )

    response = {'meta': meta, 'data': author_json}
    return jsonify(response)




@app.route('/api/volumes_by_spine')
def api_volumes_by_spine():
    # arg_sort = request.args.get('sort')
    # arg_limit = request.args.get('limit')
    # arg_offset = request.args.get('offset')
    #
    #
    # if arg_sort == 'author':
    #     query = Book.query.order_by(Book.author_last_name).order_by(Book.title)
    #
    # else:
    #     query = Book.query.order_by(Book.title)
    #
    #
    # if not arg_limit:
    #     int_limit = 50
    #
    # else:
    #     int_limit = int(arg_limit)
    #
    # if not arg_offset:
    #     int_offset = 0
    #
    # else:
    #     int_offset = int(arg_offset)
    #
    #
    # if int_limit <= 0 or int_offset < 0:
    #     return 'Invalid params'
    #
    # query = query.filter_by(public=True).limit(int_limit).offset(int_offset)


    meta = {
        # 'limit': int_limit,
        # 'offset': int_offset,
        'total': Book.query.count()
    }

    books = dict()
    query = Book.query.order_by(Book.author_last_name).order_by(Book.title)

    for item in query:
        print(item.slug)
        if item.spine_image in books and item.spine_image != '' and not item.spine_image.isspace():

            books[item.spine_image]['volumes'].append(
                {
                    'volume_number': item.volume_number,
                    'part_of_book': item.part_of_book,
                    'page_count': item.page_count,
                    'marginalia_count': item.marginalia_count,
                    'id': item.id,
                    # 'full_text_edition_link': item.full_text_edition_link,
                    # 'period_translation_link': item.period_translation_link,
                    # 'critical_intro': item.critical_intro,
                }
            )


        else:
            books[item.spine_image] = {
                    'slug': item.slug,
                    'title': item.title,
                    'subtitle': item.subtitle,
                    'author': {
                        'first_name': item.author_first_name,
                        'last_name': item.author_last_name,
                        'id': item.author.id,
                    },
                    'edition': item.edition,
                    'number_of_volumes': item.number_of_volumes,
                    'publisher': item.publisher,
                    'place_of_pub': item.place_of_pub,
                    'year_of_pub': item.year_of_pub,
                    # 'full_text_edition_link': item.full_text_edition_link,
                    # 'period_translation_link': item.period_translation_link,
                    'critical_intro': item.critical_intro,
                    'volumes': [
                            {
                                'volume_number': item.volume_number,
                                'part_of_book': item.part_of_book,
                                # 'full_text_edition_link': item.full_text_edition_link,
                                # 'period_translation_link': item.period_translation_link,
                                # 'critical_intro': item.critical_intro,
                                'page_count': item.page_count,
                                'marginalia_count': item.marginalia_count,
                                'id': item.id
                            }
                        ]
                }

    response = {'meta': meta, 'data': books}
    return jsonify(response)


@app.route('/api/volumes')
def api_volumes():
    arg_slugs = request.args.get('slugs')

    books = dict()
    books_list = []

    if arg_slugs:
        slugs_list = arg_slugs.split(' ')
        query = Book.query.filter_by(public=True).filter(Book.slug.in_(slugs_list))

    else:
        query = Book.query.filter_by(public=True)

    for item in query:
        if item.spine_image in books and item.spine_image != '' and not item.spine_image.isspace():
            int_volume_number = int(item.volume_number)

            books[item.spine_image]['volumes'][int_volume_number-1] = {
                    'volume_number': item.volume_number,
                    'part_of_book': item.part_of_book,
                    'page_count': item.page_count,
                    'marginalia_count': item.marginalia_count,
                    'id': item.id,
                    'slug': item.slug,
                }
            books[item.spine_image]['slug_set'] = books[item.spine_image]['slug_set']+'+'+item.slug

        else:
            books[item.spine_image] = {
                    'title': item.title,
                    'subtitle': item.subtitle,
                    'author': {
                        'first_name': item.author_first_name,
                        'last_name': item.author_last_name,
                        'id': item.author.id,
                    },
                    'edition': item.edition,
                    'number_of_volumes': item.number_of_volumes,
                    'publisher': item.publisher,
                    'place_of_pub': item.place_of_pub,
                    'year_of_pub': item.year_of_pub,
                    # 'full_text_edition_link': item.full_text_edition_link,
                    # 'period_translation_link': item.period_translation_link,
                    'critical_intro': item.critical_intro,
                    'slug_set': item.slug,
                    'volumes': []
                }

            int_volume_number = int(item.volume_number)
            int_number_of_volumes = int(item.number_of_volumes)

            books[item.spine_image]['volumes'] = [''] * int_number_of_volumes
            books[item.spine_image]['volumes'][int_volume_number-1] = {
                                                          'volume_number': item.volume_number,
                                                          'part_of_book': item.part_of_book,
                                                          'page_count': item.page_count,
                                                          'marginalia_count': item.marginalia_count,
                                                          'id': item.id,
                                                          'slug': item.slug,
                                                      }

    for key, value in books.items():
        books_list.append(
            {
                'spine': key,
                'title': value['title'],
                'subtitle': value['subtitle'],
                'author': value['author'],
                'edition': value['edition'],
                'number_of_volumes': value['number_of_volumes'],
                'publisher': value['publisher'],
                'place_of_pub': value['place_of_pub'],
                'year_of_pub': value['year_of_pub'],
                'critical_intro': value['critical_intro'],
                'volumes': value['volumes'],
                'slug_set': value['slug_set']
            }
        )

    meta = {
        'total': Book.query.count()
    }

    response = {'meta': meta, 'data': books_list}
    return jsonify(response)




