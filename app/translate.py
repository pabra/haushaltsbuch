import os
import imp
import pprint

from flask import g


def translate(msg):
    msg_dict = getattr(g, 'msg_dict', None)

    if msg_dict is None:
        # msg_dict = importlib.import_module('msg_%s' % g.config['LANG'])
        # exec('msg_%s.py' % g.config['LANG'])
        try:
            path = os.path.dirname(__file__)
            module_path = os.path.join(path, 'msg_%s.py' % g.config['LANG'])
            msg_module = imp.load_source('msg_dict', module_path)
            msg_dict = msg_module.msg_dict

        except FileNotFoundError:
            msg_dict = {}

        g.msg_dict = msg_dict

    msg_translated = msg_dict.get(msg)

    if msg_translated is not None:
        return msg_translated

    if g.config['DEBUG']:
        if not hasattr(g, 'missing_translations'):
            g.missing_translations = msg_dict.copy()

        if not msg in g.missing_translations:
            g.missing_translations[msg] = None
            txt = '# -*- coding: utf-8 -*-\n'
            txt += '# msg_%s.py\n\n' % g.config['LANG']
            txt += 'msg_dict = {\n'
            for k in sorted(g.missing_translations.keys(), key=lambda x: (x.lower(), x)):
                txt += '    %r: %r,\n' % (k, g.missing_translations[k])
            txt += '}\n'
            print(txt)

        return '-_%s_-' % msg

    return msg

def translate_list(l, prefix=None):
    if prefix is None:
        str_pre = ''
    else:
        str_pre = str(prefix)

    return [translate(str_pre + x) for x in l]

def get_datepicker_translations():
    monthNames = ['January', 'February', 'March',
                  'April', 'May', 'June',
                  'July', 'August', 'September',
                  'October', 'November', 'December']

    dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    dayNamesMin = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

    return {'monthNames': translate_list(monthNames),
            'dayNames': translate_list(dayNames),
            'dayNamesMin': translate_list(dayNamesMin, prefix='dayNamesMin_'),
            'nextText': translate('Next'),
            'prevText': translate('Previous')}
