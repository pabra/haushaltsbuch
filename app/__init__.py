import json

from flask import Flask, g, render_template, jsonify, request

from .translate import translate, get_datepicker_translations
from . import database
from . import update
from . import utils

app = Flask(__name__)
app.config.from_object('config')
app.jinja_env.filters['translate'] = translate
app.jinja_env.filters['json'] = json.dumps


def shutdown_server():
    fn = request.environ.get('werkzeug.server.shutdown')
    if fn is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    fn()

@app.before_request
def before_request(force=False):
    if request.endpoint == 'static' and not force:
        return

    if getattr(g, 'db', None) is None:
        g.db = database.connect_db()

    if getattr(g, 'config', None) is None:
        g.config = app.config

@app.before_first_request
def before_first_request():
    before_request(force=True)
    update.refresh()

@app.teardown_request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

@app.route('/')
@app.route('/summary.html')
def summary():
    updates_available, _ = database.kv_get('updates_available', 'int')
    categories_dict, category_ids, summary = database.get_summary()
    return render_template('summary.html', page='summary', updates_available=updates_available, categories_dict=categories_dict, category_ids=category_ids, summary=summary)

@app.route('/expense.html')
def expense_index():
    updates_available, _ = database.kv_get('updates_available', 'int')
    datepicker_locale_strings = get_datepicker_translations()
    return render_template('expense.html', page='expense', updates_available=updates_available, datepicker_locale_strings=datepicker_locale_strings)

@app.route('/category.html')
def category_index():
    updates_available, _ = database.kv_get('updates_available', 'int')
    return render_template('category.html', page='category', updates_available=updates_available)


# category REST API
@app.route('/category/get', methods=['GET'])
def category_get_all():
    return jsonify({'data': database.get_all_categories()})

@app.route('/category/update', methods=['POST'])
def category_update():
    d = {'method': request.method,
         'form': request.json,
         'action': 'update'}

    try:
        res = database.update_category(request.json)
        d.update(res)
        d['OK'] = True
        status = 200
    except AssertionError as e:
        d['OK'] = False
        d['error'] = str(e)
        status = 500

    return  jsonify(d), status

@app.route('/category/add', methods=['POST'])
def category_add():
    d = {'method': request.method,
         'form': request.json,
         'action': 'add'}

    try:
        res = database.add_category(request.json)
        d.update(res)
        d['OK'] = True
        status = 200
    except AssertionError as e:
        d['OK'] = False
        d['error'] = str(e)
        status = 500

    return jsonify(d), status

@app.route('/category/<int:category_id>', methods=['DELETE'])
def category_delete(category_id):
    d = {'method': request.method,
         'category_id': category_id,
         'action': 'delete'}

    try:
        database.delete_category(category_id)
        d['OK'] = True
        status = 200
    except AssertionError as e:
        d['OK'] = False
        d['error'] = str(e)
        status = 500

    return jsonify(d), status


# expense REST API
@app.route('/expense/get', methods=['GET'])
def expense_get_all():
    order_by_list = utils.get_order_by_from_request(request)
    filter_list = utils.get_filter_from_request(request)

    return jsonify({'data': database.date_to_json(
        database.get_all_expenses(order_by=order_by_list,
                                  filter_by=filter_list)
    )})

@app.route('/expense/update', methods=['POST'])
def expense_update():
    d = {'method': request.method,
         'form': request.json,
         'action': 'update'}

    try:
        data = database.json_to_date(request.json)
        res = database.update_expense(data)
        d.update(res)
        d['OK'] = True
        status = 200
    except (AssertionError, ValueError) as e:
        d['OK'] = False
        d['error'] = str(e)
        status = 500

    return  jsonify(database.date_to_json(d)), status

@app.route('/expense/add', methods=['POST'])
def expense_add():
    d = {'method': request.method,
         'form': request.json,
         'action': 'add'}

    try:
        data = database.json_to_date(request.json)
        res = database.add_expense(data)
        d.update(res)
        d['OK'] = True
        status = 200
    except (AssertionError, ValueError) as e:
        d['OK'] = False
        d['error'] = str(e)
        status = 500

    return jsonify(database.date_to_json(d)), status

@app.route('/expense/<int:expense_id>', methods=['DELETE'])
def expense_delete(expense_id):
    d = {'method': request.method,
         'expense_id': expense_id,
         'action': 'delete'}

    try:
        database.delete_expense(expense_id)
        d['OK'] = True
        status = 200
    except AssertionError as e:
        d['OK'] = False
        d['error'] = str(e)
        status = 500

    return jsonify(d), status


# summary REST API
@app.route('/summary/get', methods=['GET'])
def summary_get_all():

    categories_dict, category_ids, summary = database.get_summary()
    return jsonify({'categories_dict': categories_dict,
                    'category_ids': category_ids,
                    'summary': summary})

@app.route('/summary/get/<int:year>', methods=['GET'])
def summary_get_year(year):
    categories_dict, category_ids, summary = database.get_summary(year)
    return jsonify({'summary': summary})

# update page
@app.route('/update.html')
def update_route():
    updates_available, _ = database.kv_get('updates_available', 'int')
    last_check, _ = database.kv_get('updates_checked', 'date')
    last_check_js = database.date_to_json([last_check])[0]
    commits_behind = []
    error_msg = None
    try:
        commits_behind = update.get_commits_behind()
    except update.UpdateException as e:
        error_msg = str(e)

    return render_template('update.html',
                           page='update',
                           updates_available=updates_available,
                           last_checked=last_check_js,
                           commits_behind=commits_behind,
                           error_msg=error_msg)

@app.route('/update/check', methods=['PUT'])
def update_check():
    update.refresh(force=True)

    return jsonify({'OK': True,
                    'status': 200})

@app.route('/update/do', methods=['PUT'])
def update_do():
    update.update()
    shutdown_server()

    return jsonify({'OK': True,
                    'status': 200})


# feed the autocomplete
@app.route('/expense_notes/<int:category_id>/<txt>', methods=['GET'])
def expense_notes(category_id, txt):
    notes = database.get_notes_of_category(category_id=category_id, txt=txt)

    return jsonify({'OK': True,
                    'status': 200,
                    'notes': notes})
