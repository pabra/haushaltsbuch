import datetime
import json
import re


def get_order_by_from_request(req):
    order_by_list = []

    for order in req.args.getlist("orderBy"):
        order_tuple = tuple(json.loads(order))

        if len(order_tuple) != 2:
            raise TypeError("Order must have a length of 2: %r" % (order_tuple,))

        if not all(isinstance(x, str) for x in order_tuple):
            raise TypeError("Order must consist of 2 strings: %r" % (order_tuple,))

        if not order_tuple[1] in ("asc", "desc"):
            raise ValueError(
                'Order direction must be one of ("asc", "desc"), not: %r'
                % (order_tuple[1],)
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", order_tuple[0]):
            raise ValueError(
                'Order field must match regex "^[a-zA-Z0-9_]+$": %r' % (order_tuple[0],)
            )

        order_by_list.append(order_tuple)

    return order_by_list


def get_filter_from_request(req):
    filter_list = []
    compare_symbols = ("<", "<=", "=", ">=", ">", "<>")
    filter_parsers = {"date": parse_filter_value_date}

    for flt in req.args.getlist("filter"):
        filter_tuple = tuple(json.loads(flt))

        if len(filter_tuple) != 3:
            raise TypeError("Filter must have a length of 3: %r" % (filter_tuple,))

        if not all(isinstance(x, str) for x in filter_tuple):
            raise TypeError("Filter must consist of 3 strings: %r" % (filter_tuple,))

        if not re.match(r"^[a-zA-Z0-9_]+$", filter_tuple[0]):
            raise ValueError(
                'Filter field must match regex "^[a-zA-Z0-9_]+$": %r'
                % (filter_tuple[0],)
            )

        if not filter_tuple[1] in compare_symbols:
            raise ValueError(
                "Filter must use allowed compare symbol %r: %r"
                % (compare_symbols, filter_tuple[1])
            )

        if not filter_tuple[0] in filter_parsers:
            raise ValueError(
                "No parser defined to filter field %r." % (filter_tuple[0],)
            )

        # if not re.match(r'^[a-zA-Z0-9._-]+$', filter_tuple[2]):
        #     raise ValueError('Filter value must match regex "^[a-zA-Z0-9._-]+$": %r' % (filter_tuple[2],))

        filter_field = filter_tuple[0]
        filter_compare = filter_tuple[1]
        filter_value = filter_parsers[filter_tuple[0]](filter_tuple[2])

        filter_list.append((filter_field, filter_compare, filter_value))

    return filter_list


def parse_filter_value_date(val):
    timestamp = datetime.datetime.strptime(val, "%Y-%m-%d")

    return timestamp.date()
