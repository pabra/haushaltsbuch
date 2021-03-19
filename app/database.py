import re
import random
import sqlite3
import datetime
from contextlib import closing
from flask import g

from .translate import translate

DB_DATE_FORMAT = "%Y-%m-%d"
DB_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def index_by(l, key):
    return {x[key]: x for x in l}


def date_to_json(thing):
    def _walk_through_dict(d):
        for k, v in d.items():
            if isinstance(v, datetime.date):
                d[k] = v.strftime(DB_DATE_FORMAT)
            elif isinstance(v, dict):
                d[k] = _walk_through_dict(v)
            elif isinstance(v, list):
                d[k] = _walk_through_list(v)

        return d

    def _walk_through_list(l):
        for k, v in enumerate(l):
            if isinstance(v, datetime.date):
                l[k] = v.strftime(DB_DATE_FORMAT)
            elif isinstance(v, dict):
                l[k] = _walk_through_dict(v)
            elif isinstance(v, list):
                l[k] = _walk_through_list(v)

        return l

    if isinstance(thing, datetime.date):
        thing = thing.strftime(DB_DATE_FORMAT)
    elif isinstance(thing, dict):
        thing = _walk_through_dict(thing)
    elif isinstance(thing, list):
        thing = _walk_through_list(thing)

    return thing


def json_to_date(data):
    for k, v in data.items():
        if k.endswith("date"):
            data[k] = datetime.datetime.strptime(v, DB_DATE_FORMAT).date()

    return data


def is_valid_color(color):
    pat = r"^#[0-9A-Fa-f]{6}$"

    return bool(re.match(pat, color))


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]

    return d


def connect_db():
    from . import app

    conn = sqlite3.connect(
        app.config["DATABASE"],
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = dict_factory

    return conn


def init_db():
    from . import app

    with closing(connect_db()) as db:
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
            db.commit()


def insert_rand():
    # from . import app
    global g
    del g

    class g(object):
        pass

    with closing(connect_db()) as db:
        g.db = db
        cat_names = [x["name"] for x in get_all_categories()]
        colors = (
            "#e06666",
            "#f6b26b",
            "#ffd966",
            "#b6d7a8",
            "#76a5af",
            "#6fa8dc",
            "#8e7cc3",
            "#c27ba0",
        )
        i = 1
        inserted = 0
        while inserted < len(colors):
            name = "cat %s" % i
            if not name in cat_names:
                add_category({"name": name, "color": colors[inserted]})
                inserted += 1
                print("inserted: %r" % name)

            i += 1

        categories = get_all_categories()
        i = 0
        while i < 1000:
            data = {
                "date": datetime.date.today()
                - datetime.timedelta(days=random.randint(1, 500)),
                "value": random.randint(50, 5000),
                "category_id": random.choice([x["id"] for x in categories]),
                "note": "insert %s" % i,
            }
            print(add_expense(data))
            i += 1


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def update_db(query, args=()):
    cur = g.db.execute(query, args)
    rowcount = cur.rowcount
    cur.close()
    g.db.commit()
    return rowcount


def insert_db(query, args=()):
    cur = g.db.execute(query, args)
    lastrowid = cur.lastrowid
    cur.close()
    g.db.commit()
    return lastrowid


# handlers for key value store
def kv_get(key, cast=None):
    assert cast in (type(None), "date", "datetime", "int")
    changed = None
    value = None
    q = "SELECT value, changed FROM kv_store WHERE key = ?"
    res = query_db(q, (key,), one=True)
    if res:
        changed = datetime.datetime.strptime(res["changed"], DB_DATETIME_FORMAT)
        if cast == "date":
            value = datetime.datetime.strptime(res["value"], DB_DATE_FORMAT).date()
        elif cast == "datetime":
            value = datetime.datetime.strptime(res["value"], DB_DATETIME_FORMAT)
        elif cast == "int":
            value = int(res["value"])
        else:
            value = res["value"]

    return value, changed


def kv_put(key, value, cast=None):
    assert cast in (type(None), "date", "datetime", "int")
    if cast == "date":
        assert isinstance(value, datetime.date)
        value = value.strftime(DB_DATE_FORMAT)
    elif cast == "datetime":
        assert isinstance(value, datetime.datetime)
        value = value.strftime(DB_DATETIME_FORMAT)
    elif cast == "int":
        assert isinstance(value, int)
        value = str(value)

    q = """
        UPDATE kv_store
        SET value = ?,
            changed = ?
        WHERE key = ?
    """
    now = datetime.datetime.now().strftime(DB_DATETIME_FORMAT)
    res = update_db(q, (value, now, key))
    print("update resp: %r" % res)
    if 0 == res:
        q = """
            INSERT INTO kv_store
            (key, value, changed)
            VALUES
            (?, ?, ?)
        """
        res = insert_db(q, (key, value, now))
        print("insert resp: %r" % res)


# manage categories
def get_all_categories():
    q = """SELECT id, name, color
           FROM category
           ORDER BY name"""

    return query_db(q)


def get_category_by_name(category_name):
    q = """SELECT id, name, color
           FROM category
           WHERE name = ?"""

    return query_db(q, (category_name,), one=True)


def get_category_by_id(category_id):
    assert isinstance(category_id, int), translate(
        "category_id must be integer not %r"
    ) % type(category_id)

    q = """SELECT id, name, color
           FROM category
           WHERE id = ?"""

    return query_db(q, (category_id,), one=True)


def delete_category(category_id):
    assert isinstance(category_id, int), translate(
        "category_id must be integer not %r"
    ) % type(category_id)

    cat = get_category_by_id(category_id)

    assert cat, "No category with id %r" % category_id

    # check if category is used in expense table
    exp = get_expense_by_category(category_id)

    assert not exp, translate(
        "cannot delete category %(category_name)r with %(nr_of_expenses)s expenses assigned"
    ) % {"category_name": cat["name"], "nr_of_expenses": len(exp)}

    q = """DELETE FROM category
           WHERE id = ?"""

    res = update_db(q, (cat["id"],))

    return {"rows": res}


def add_category(data):
    assert isinstance(data, dict), translate("data must be dict not %r") % type(data)
    assert "name" in data, translate('data dict must have a "name" entry')
    assert "color" in data, translate('data dict must have a "color" entry')

    name = data["name"].strip()
    color = data["color"].strip()

    assert name, translate("name must not be empty")
    assert color, translate("color must not be empty")
    assert isinstance(name, str), translate("name must be string not %r") % type(name)
    assert isinstance(color, str), translate("color must be string not %r") % type(
        color
    )
    assert is_valid_color(color), (
        translate("value of color does not look valid: %r") % color
    )

    cat = get_category_by_name(name)

    assert not cat, translate("category already exists %r") % cat

    q = """INSERT INTO category
           (name, color)
           VALUES
           (?, ?)"""

    res = insert_db(q, (name, color))

    return {"id": res, "data": get_category_by_id(res)}


def update_category(data):
    assert isinstance(data, dict), translate("data must be dict not %r") % type(data)
    category_id = data.get("id")
    assert isinstance(category_id, int), translate(
        "category_id must be integer not %r"
    ) % type(category_id)

    cat = get_category_by_id(category_id)

    assert cat, translate("No category with id %r") % category_id

    q_pre = "UPDATE category SET "
    q_suf = " WHERE id = ?"
    q_mid = []
    q_arg = ()

    if "name" in data:
        name = data["name"].strip()
        assert name, translate("name must not be empty")
        assert isinstance(name, str), translate("name must be string not %r") % type(
            name
        )

        dup_cat = get_category_by_name(name)
        # ignore own name
        if dup_cat and dup_cat["id"] == category_id:
            dup_cat = None

        assert not dup_cat, translate(
            "category already exists %(existing)r, %(duplicate)r"
        ) % {"existing": cat, "duplicate": dup_cat}

        q_mid.append("name = ?")
        q_arg += (name,)

    if "color" in data:
        color = data["color"].strip()
        assert color, translate("color must not be empty")
        assert isinstance(color, str), translate("color must be string not %r") % type(
            color
        )
        assert is_valid_color(color), (
            translate("value of color does not look valid %r") % color
        )

        q_mid.append("color = ?")
        q_arg += (color,)

    if q_mid:
        q = q_pre + ", ".join(q_mid) + q_suf
        res = update_db(q, q_arg + (cat["id"],))

        return {"rows": res, "data": get_category_by_id(category_id)}


# manage expenses
def get_all_expenses(order_by=[("date", "asc")], filter_by=[]):
    q_args = []
    order_by = [
        ("category_id", order[1]) if order[0] == "category" else order
        for order in order_by
    ]

    order_by_str = ", ".join(["%s %s" % order for order in order_by])

    order_by_q = ""
    if order_by_str:
        order_by_q = "ORDER BY " + order_by_str

    filter_by_str = " AND ".join(["%s %s ?" % flt[:2] for flt in filter_by])

    q_args.extend([x[2] for x in filter_by])

    filter_by_q = ""
    if filter_by_str:
        filter_by_q = "WHERE " + filter_by_str

    q = """SELECT id, date, value, note, category_id
           FROM expense
           %s
           %s""" % (
        filter_by_q,
        order_by_q,
    )

    print(q, q_args)

    return query_db(q, tuple(q_args))


def get_expense_by_id(expense_id):
    assert isinstance(expense_id, int), translate(
        "expense_id must be integer not %r"
    ) % type(expense_id)

    q = """SELECT id, date, value, note, category_id
           FROM expense
           WHERE id = ?"""

    return query_db(q, (expense_id,), one=True)


def get_expense_by_category(category_id):
    assert isinstance(category_id, int), translate(
        "category_id must be integer not %r"
    ) % type(category_id)

    q = """SELECT id, date, value, note, category_id
           FROM expense
           WHERE category_id = ?"""

    return query_db(q, (category_id,))


def delete_expense(expense_id):
    assert isinstance(expense_id, int), translate(
        "expense_id must be integer not %r"
    ) % type(expense_id)

    exp = get_expense_by_id(expense_id)

    assert exp, translate("no expense with id %r") % expense_id

    q = """DELETE FROM expense
           WHERE id = ?"""

    res = update_db(q, (exp["id"],))

    return {"rows": res}


def update_expense(data):
    assert isinstance(data, dict), translate("data must be dict not %r") % type(data)
    expense_id = data.get("id")
    assert isinstance(expense_id, int), translate(
        "expense_id must be integer not %r"
    ) % type(expense_id)

    exp = get_expense_by_id(expense_id)

    assert exp, translate("no expense with id %r") % expense_id

    q_pre = "UPDATE expense SET "
    q_suf = " WHERE id = ?"
    q_mid = []
    q_arg = ()

    if "date" in data:
        date = data["date"]
        assert isinstance(date, datetime.date), translate(
            "date must be datetime.date not %r"
        ) % type(date)

        q_mid.append("date = ?")
        q_arg += (date,)

    if "category_id" in data:
        category_id = data["category_id"]
        assert isinstance(category_id, int), translate(
            "category_id must be integer not %r"
        ) % type(category_id)

        cat = get_category_by_id(category_id)

        assert cat, translate("No category with id %r") % category_id

        q_mid.append("category_id = ?")
        q_arg += (cat["id"],)

    if "value" in data:
        value = data["value"]
        assert isinstance(value, int), "value must be integer not %r" % type(value)

        q_mid.append("value = ?")
        q_arg += (value,)

    if "note" in data:
        note = data["note"]
        assert isinstance(
            note, (str, type(None))
        ), "note must be string or None not %r" % type(note)

        if isinstance(note, str):
            if not note.strip():
                note = None

        q_mid.append("note = ?")
        q_arg += (note,)

    if q_mid:
        q = q_pre + ", ".join(q_mid) + q_suf
        res = update_db(q, q_arg + (exp["id"],))

        return {"rows": res, "data": get_expense_by_id(expense_id)}


def add_expense(data):
    assert isinstance(data, dict), translate("data must be dict not %r") % type(data)

    assert "date" in data, translate('data dict must have a "date" entry')
    assert "category_id" in data, translate('data dict must have a "category_id" entry')
    assert "value" in data, translate('data dict must have a "value" entry')

    date = data["date"]
    assert isinstance(date, datetime.date), translate(
        "date must be datetime.date not %r"
    ) % type(date)

    category_id = data["category_id"]
    assert isinstance(category_id, int), translate(
        "category_id must be integer not %r"
    ) % type(category_id)
    cat = get_category_by_id(category_id)
    assert cat, translate("No category with id %r") % category_id

    value = data["value"]
    assert isinstance(value, int), "value must be integer not %r" % type(value)

    note = None
    if "note" in data and data["note"].strip():
        note = data["note"].strip()

    q = """INSERT INTO expense
           (date, category_id, value, note)
           VALUES
           (?, ?, ?, ?)"""

    res = insert_db(q, (date, category_id, value, note))

    return {"id": res, "data": get_expense_by_id(res)}


def get_summary(year=None):
    assert isinstance(year, (int, type(None)))
    categories = get_all_categories()

    if 0 == len(categories):
        return {}, [], []

    q = """
        SELECT
            category_id,
            SUM(value) AS value_total,
            %s,
            COUNT(id) AS count_total,
            %s,
            %s
            CAST(STRFTIME('%%Y', date) AS INTEGER) AS year
        FROM expense
        %s
        GROUP BY strftime('%s', date)
        ORDER BY date ASC
    """ % (
        ", ".join(
            (
                "SUM(CASE category_id WHEN %(id)s THEN value ELSE 0 END) AS value_%(id)s"
                % cat
                for cat in categories
            )
        ),
        ", ".join(
            (
                "SUM(CASE category_id WHEN %(id)s THEN 1 ELSE 0 END) AS count_%(id)s"
                % cat
                for cat in categories
            )
        ),
        "" if year is None else 'CAST(STRFTIME("%m", date) AS INTEGER) AS month,',
        "" if year is None else 'WHERE STRFTIME("%%Y", date) = "%s"' % year,
        "%Y" if year is None else "%Y-%m",
    )

    return index_by(categories, "id"), [x["id"] for x in categories], query_db(q)


def get_notes_of_category(category_id, txt):
    q = """
        SELECT DISTINCT note
        FROM expense
        WHERE category_id = ?
          AND note LIKE ?
        ORDER BY note ASC
        LIMIT 15
    """
    res = query_db(q, (category_id, "%" + txt + "%"))

    return [x["note"] for x in res]
