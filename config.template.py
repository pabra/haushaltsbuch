#
# kopiere diese Vorlage, speichere sie als config.py und passe die Werte deinen Bedürfnissen an
#
# make a copy of this template, save it is config.py and set values for your needs
#

DATABASE = "./data.sqlite3"
HOST = "127.0.0.1"
PORT = 5000
DEBUG = True
# LANG must be one of ('en', 'de')
LANG = "en"
# see possible formats here: http://api.jqueryui.com/datepicker/#utility-formatDate
DATEPICKER_DATE_FORMAT = "yy-mm-dd"
# sunday: 0, monday: 1
DATEPICKER_FIRST_DAY_OF_WEEK = 0
DECIMAL_CHAR = "."
THOUSANDS_SEPARATOR = ","
CURRENCY_SYMBOL = "$"
# should the currency symbol be printed before the value (eg: "$ 123") set this to True
# for a trailing currency symbol (eg: "123 €") set this to False
CURRENCY_SYMBOL_LEAD = True

# how often should we check for updates (in days)?
# -1 = never
# 0  = every time the program starts
# 1  = once per day
# 7  = every week
# and so on
CHECK_FOR_UPDATES = 1
