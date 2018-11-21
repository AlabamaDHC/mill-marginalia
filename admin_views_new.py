from flask import render_template, request, flash, redirect, url_for, jsonify, json

from sqlalchemy.orm import joinedload, load_only, Load
from sqlalchemy.testing.plugin.plugin_base import options

from app import app, db
# from models import User, Role, Book, Page, Marginalia, Author
from models.author import Author
from models.book import Book
from models.page import Page
from models.marginalia import Marginalia
from models.import_models import ImportItem

@app.route('/authors/edit')
def show_edit_authors():
    authors = Author.query.order_by(Author.last_name)
    return render_template('front/authors.html', authors=authors, edit=True, api_route='api/authors')


@app.route('/authors/edit/<author_id>', methods=['GET', 'POST'])
def edit_author(author_id):
    if request.method == 'GET':
        return render_template('admin/authors.html', api_route='api/authors/'+author_id)

    if request.method == 'POST':
        return render_template('admin/authors.html', api_route='api/authors/'+author_id)




@app.route('/library/multivol/<slugs>/edit')
def edit_book_multi_vol(slugs):
    return render_template('admin/volumes.html', args='?slugs='+slugs, sort='none', page_header='Selected Volumes')
