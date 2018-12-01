/* global ko, page, tinycolor, categoryTranslate, datepickerDateFormat, datepickerFirstDayOfWeek,
          thousandsSeparator, decimalChar, currencySymbol, currencySymbolLead,
          datepickerLocaleStrings */

/**
 * requires:
 * - jQuery
 * - jQuery UI (Datepicker, Autocomplete, Button)
 * - knockoutjs
 * - spectrum.js (color picker)
 */
$(function() {
    'use strict';
    var isInt, initColorPicker, initDatePicker, getItemObservable, getItemJson,
        itemChanged, itemReset, itemUpdate, itemDelete, itemAdd,
        listSort, CategoryModel, categoryModel, ExpenseModel, expenseModel,
        SummaryModel, summaryModel,
        formatCurrencyValue, parseCurrencyValue,
        getFirstOfMonth, getLastOfMonth, unsetTimeOfDate;

    isInt = function (n){
        return Number(n) === n && n % 1 === 0;
    };

    initColorPicker = function(el, item) {
        var tc;

        if(!el.length) {
            return;
        }

        item._colorPicker = el;
        el.spectrum({
            showPaletteOnly: true,
            showPalette: true,
            hideAfterPaletteSelect: true,
            palette: [
                ["#000000","#444444","#666666","#999999","#cccccc","#eeeeee","#f3f3f3","#ffffff"],
                // ["#ff0000","#ff9900","#ffff00","#00ff00","#00ffff","#000fff","#9900ff","#ff00ff"],
                ["#f4cccc","#fce5cd","#fff2cc","#d9ead3","#d0e0e3","#cfe2f3","#d9d2e9","#ead1dc"],
                ["#ea9999","#f9cb9c","#ffe599","#b6d7a8","#a2c4c9","#9fc5e8","#b4a7d6","#d5a6bd"],
                ["#e06666","#f6b26b","#ffd966","#93c47d","#76a5af","#6fa8dc","#8e7cc3","#c27ba0"],
                ["#cc0000","#e69138","#f1c232","#6aa84f","#45818e","#3d85c6","#674ea7","#a64d79"],
                ["#990000","#b45f06","#bf9000","#38761d","#134f5c","#0b5394","#351c75","#741b47"],
                ["#660000","#783f04","#7f6000","#274e13","#0c343d","#073763","#20124d","#4c1130"]
            ]
        }).on('change.spectrum', function(ev, tc) {
            // tc -> tinycolor
            item.color(tc.toHexString());
            item.isDark(tc.isDark());
        });
        tc = el.spectrum('get');
        item.isDark(tc.isDark());
    };

    initDatePicker = function(el, item) {
        var datepickerOptions = {
            showOtherMonths: true,
            selectOtherMonths: true,
            dateFormat: datepickerDateFormat,
            firstDay: datepickerFirstDayOfWeek
        };

        if(datepickerLocaleStrings) {
            $.extend(datepickerOptions, datepickerLocaleStrings);
        }

        if(!el.length) {
            return;
        }

        item._datePicker = el;
        el.datepicker(datepickerOptions);
    };

    unsetTimeOfDate = function(dateObj) {
        if (!(dateObj instanceof Date)) throw new TypeError('expected Date object');

        dateObj.setMilliseconds(0);
        dateObj.setSeconds(0);
        dateObj.setMinutes(0);
        dateObj.setHours(0);

        return dateObj;
    };

    getFirstOfMonth = function(dateObj) {
        if (!(dateObj instanceof Date)) {
            dateObj = new Date();
        }

        dateObj.setDate(1);

        return unsetTimeOfDate(dateObj);
    };

    getLastOfMonth = function(dateObj) {
        var firstOfNextMonth;

        if (!(dateObj instanceof Date)) {
            dateObj = new Date();
        }

        // add 32 days because in case of daylight saving there can be one hour missing
        firstOfNextMonth = getFirstOfMonth(
            new Date(getFirstOfMonth(dateObj).getTime() + 32 * 24 * 60 * 60 * 1000)
        );

        return unsetTimeOfDate(new Date(firstOfNextMonth.getTime() - 12 * 60 * 60 * 1000));
    };

    itemUpdate = function(item) {
        var itemData = item._getJsonChanged();

        itemData.id = item.id();
        item._error('');
        $.ajax({
            url: '/' + item._type + '/update',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(itemData),
            success: function(data) {
                var newItem = getItemObservable(data.data, item._type, item._superList, item._preFn, item._postFn);
                item._superList.remove(item);
                item._superList.push(newItem);
            },
            error: function(data) {
                if(data.responseJSON.error) {
                    item._error(data.responseJSON.error);
                }
            }
        });
    };

    itemDelete = function(item) {
        item._error('');
        $.ajax({
            url: '/' + item._type + '/' + item.id(),
            method: 'DELETE',
            success: function(data) {
                if(data.OK) {
                    item._superList.remove(item);
                }
            },
            error: function(data) {
                if(data.responseJSON.error) {
                    item._error(data.responseJSON.error);
                }
            }
        });
    };

    itemAdd = function(item) {
        item._error('');
        $.ajax({
            url: '/' + item._type + '/add',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(item._getJsonAll()),
            success: function(data) {
                var newItem = getItemObservable(data.data, item._type, item._superList, item._preFn, item._postFn);
                item._reset(item);
                item._superList.push(newItem);
                window.setTimeout(function() {
                    $(window).scrollTop(9999999);
                }, 0);
            },
            error: function(data) {
                if(data.responseJSON.error) {
                    item._error(data.responseJSON.error);
                }
            }
        });
    };

    itemReset = function(item) {
        item._error('');
        item._edit(false);
        ko.utils.objectForEach(item, function(k, v) {
            if(ko.isObservable(v) && undefined !== v._default) {
                v(v._default);
            }
            if('color' === k && item._colorPicker) {
                item._colorPicker.spectrum('set', item[k]._default);
            }
        });
    };

    itemChanged = function(newVal) {
        var item = this,
            anyChange = false;

        ko.utils.objectForEach(item, function(k, v) {
            if(ko.isObservable(v) && undefined !== v._default && v() !== v._default) {
                anyChange = true;
            }
        });

        item._changed(anyChange);
    };

    getItemJson = function(item, onlyChanged) {
        var json = {};

        ko.utils.objectForEach(item, function(k, v) {
            if(ko.isObservable(v) && undefined !== v._default && (!onlyChanged || v() !== v._default)) {
                json[k] = v();
            }
        });

        return json;
    };

    getItemObservable = function(item, type, superList, preFn, postFn) {
        /*  type:
         *      type of the item
         *      used to get/post/update items
         *  superList:
         *      ko.observableArray that will holds this item
         *  preFn:
         *      function to call before item is observable (will get item as arg)
         *  postFn:
         *      function to call after item is observable (will get newItem as arg)
         */
        var newItem = {_type: type,
                       _superList: superList,
                       _preFn: preFn,
                       _postFn: postFn,
                       _edit: ko.observable(false),
                       _beEditable: function() { this._error(''); this._edit(true); },
                       _changed: ko.observable(false),
                       _error: ko.observable(''),
                       _reset: itemReset,
                       _add: itemAdd,
                       _update: itemUpdate,
                       _delete: itemDelete,
                       _getJsonChanged: function() { return getItemJson(newItem, true); },
                       _getJsonAll: function() { return getItemJson(newItem); }};

        if(preFn instanceof Function) {
           preFn(item);
        }

        ko.utils.objectForEach(item, function(k, v) {
            if('_' === k.substr(0, 1)) {
                // no underscore observables
                return;
            }
            if(undefined !== newItem[k]) {
                throw 'key ' + k + ' already exists.';
            }
            newItem[k] = ko.observable(v);
            newItem[k].subscribe(itemChanged, newItem);
            newItem[k]._default = v;
        });

        if(postFn instanceof Function) {
            postFn(newItem);
        }

        return newItem;
    };

    listSort = function(list, orderBy) {
        list.sort(function(a, b) {
            if(a.id() === -1) return 1;
            if(b.id() === -1) return -1;
            if(a[orderBy]() === b[orderBy]()) return 0;
            if(a[orderBy]() <  b[orderBy]()) return -1;
            return 1;
        });
    };

    parseCurrencyValue = function(val) {
        var re = new RegExp('[ ' + currencySymbol + thousandsSeparator + ']', 'g'),
            replaced = val.replace(re, ''),
            splitted = replaced.split(decimalChar),
            major = '0' + (splitted[0] || ''),
            minor = ((splitted[1] || '') + '00').substr(0, 2),
            asInt = parseInt(major + minor, 10);

        return asInt;
    };

    formatCurrencyValue = function(val) {
        var major = new String(Math.floor(val / 100)),
            minor = ('0' + new String(val % 100)).substr(-2),
            s;

        major = major.replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
        s = major + decimalChar + minor;

        if(currencySymbolLead) {
            s = currencySymbol + ' ' + s;
        } else {
            s = s + ' ' + currencySymbol;
        }

        return s;
    };


    if('category' === page){
        CategoryModel = function() {
            var self = this,
                newColor = '#ffffff',
                preObservableFn, postObservableFn, init;

            self.categories = ko.observableArray();
            self.categories.subscribe(function(list) { listSort(list, 'name'); });

            self.afterRender = function(el, item) {
                initColorPicker($(el).find('input[type=color]'), item);
            };

            preObservableFn = function(item) {
                item.isDark = tinycolor(item.color).isDark();
            };

            postObservableFn = function(item) {
                item._edit.subscribe(function(newVal) {
                    if(newVal) {
                        window.setTimeout(function() {
                            var el = $('input[type=color].category_' + item.id());
                            initColorPicker(el, item);
                        }, 0);
                    } else {
                        if(item._colorPicker && item._colorPicker.spectrum('get') instanceof tinycolor) {
                            item._colorPicker.spectrum('destroy');
                        }
                    }
                });
            };

            init = function() {
                $.getJSON('/' + page + '/get', function(data) {
                    var list = [];
                    ko.utils.arrayForEach(data.data, function(item) {
                        list.push(getItemObservable(item, page, self.categories, preObservableFn, postObservableFn));
                    });
                    list.push(getItemObservable({color: newColor, id: -1, name: ''}, page, self.categories, preObservableFn, postObservableFn));
                    self.categories(list);
                });
            };

            init();
        };

        categoryModel = new CategoryModel();
        window.debug_categoryModel = categoryModel;
        ko.applyBindings(categoryModel);
    }

    if('expense' === page) {
        ExpenseModel = function() {
            var self = this,
                initialSorting = [['date', 'asc']],
                isInitialSorting = true,
                initialFilter = [['date', '>=', $.datepicker.formatDate('yy-mm-dd', getFirstOfMonth())]],
                preExpensesObservableFn, postExpensesObservableFn,
                initExpenses, initCategories, bindInputWidgets,
                isFieldSorted, setFieldSorted, getSortedChar;

            self.expenses = ko.observableArray();
            self.categories = ko.observableArray();
            self.categoriesById = {};
            self.orderBy = ko.observableArray(initialSorting).extend({hashSync: 'orderBy'});
            self.orderBy.subscribe(function() { initExpenses(); });
            self.sortedDateChar = ko.pureComputed(function() { return getSortedChar(isFieldSorted('date')); });
            self.sortedValueChar = ko.pureComputed(function() { return getSortedChar(isFieldSorted('value')); });
            self.sortedCategoryChar = ko.pureComputed(function() { return getSortedChar(isFieldSorted('category')); });
            self.sortedNoteChar = ko.pureComputed(function() { return getSortedChar(isFieldSorted('note')); });
            self.filter = ko.observableArray(initialFilter).extend({hashSync: 'filter'});
            self.filter.subscribe(function() { initExpenses(); });

            self.afterRender = function(el, item) {
                bindInputWidgets(item);
            };

            self.selectAll = function(item, ev) {
                $(ev.target).select();
            };

            self.sortClick = function(model, ev) {
                var el = $(ev.target),
                    name = el.attr('name'),
                    isSorted = isFieldSorted(name),
                    willSort = 'asc' === isSorted ? 'desc' : 'asc';

                setFieldSorted(name, willSort);
            };

            self.removeFromSorting = function(sortItem) {
                setFieldSorted(sortItem[0], null);
            };

            self.removeFromFilter = function(filterItem) {
                self.filter.remove(filterItem);
            };

            isFieldSorted = function(name) {
                var isSorted = null;

                ko.utils.arrayForEach(self.orderBy(), function(x) {
                    if (x[0] === name) {
                        isSorted =  x[1];
                    }
                });

                return isSorted;
            };

            setFieldSorted = function(name, direction) {
                var newSorted = [],
                    nameFound = false;

                if (!isInitialSorting || null === direction) {
                    ko.utils.arrayForEach(self.orderBy(), function(x) {
                        if (x[0] === name) {
                            nameFound = true;
                            if (null !== direction) {
                                newSorted.push([name, direction]);
                            }
                        } else {
                            newSorted.push(x);
                        }
                    });
                }

                if (!nameFound) {
                    newSorted.push([name, direction]);
                    isInitialSorting = false;
                }

                if (0 === newSorted.length) {
                    newSorted = initialSorting;
                    isInitialSorting = true;
                }

                self.orderBy(newSorted);
            };

            getSortedChar = function(direction) {
                return direction === 'asc' ? '&uarr;' :
                       direction === 'desc' ? '&darr;' : '';
            };

            bindInputWidgets = function(item) {
                var elDate = $('input.expense_date_' + item.id()),
                    elNote = $('input.expense_note_' + item.id());

                initDatePicker(elDate, item);
                elNote.autocomplete({
                    minLength: 1,
                    source: function(req, res) {
                        var category_id = item.category_id();

                        if (!isInt(category_id) || !req.term) {
                            return;
                        }
                        $.getJSON('/expense_notes/' + category_id + '/' +  encodeURIComponent(req.term), function(data) {
                            res(data.notes);
                        });
                    },
                    select: function(ev, ui) {
                        $(ev.target)
                            .val(ui.item.value)
                            .change();
                        return false;
                    },
                    open: function(ev, ui) {
                        var inputEl = $(ev.target),
                            inputTop = inputEl.position().top,
                            inputHeight = inputEl.outerHeight(),
                            win = $(window),
                            spaceBelow = (win.scrollTop() + win.height()) - (inputTop + inputHeight),
                            popupEl = inputEl.autocomplete("widget"),
                            popupHeight = popupEl.outerHeight(),
                            aboveTop = inputTop - popupHeight;

                        if (popupHeight >= spaceBelow) {
                            popupEl.css({top: aboveTop + 'px'});
                        }
                    }
                });
            };

            preExpensesObservableFn = function(item) {
                var parsedDate = $.datepicker.parseDate('yy-mm-dd', item.date),
                    localDate = $.datepicker.formatDate(datepickerDateFormat, parsedDate);

                item.localDate = localDate;
                item.localValue = formatCurrencyValue(item.value);
            };

            postExpensesObservableFn = function(item) {
                item.isDark = ko.pureComputed(function() {
                    var tc = tinycolor(self.categoriesById[item.category_id()].color);
                    return tc.isDark();
                });

                item.color = ko.pureComputed(function() {
                    var cat = self.categoriesById[item.category_id()];
                    return cat ? cat.color : '';
                });

                item.localDate.subscribe(function(newVal) {
                    var parsedDate = $.datepicker.parseDate(datepickerDateFormat, newVal),
                        isoDate = $.datepicker.formatDate('yy-mm-dd', parsedDate);
                    item.date(isoDate);
                });

                item.localValue.subscribe(function(newVal) {
                    var intVal = parseCurrencyValue(newVal);

                    if(newVal === '') {
                        item.value(newVal);
                    } else if(isNaN(intVal)) {
                        item.localValue(0);
                    } else {
                        item.value(intVal);
                        item.localValue(formatCurrencyValue(intVal));
                    }
                });

                item._edit.subscribe(function(newVal) {
                    if(newVal) {
                        window.setTimeout(function() {
                            bindInputWidgets(item);
                        }, 0);
                    } else {
                        if(item._datePicker) {
                            item._datePicker.datepicker('destroy');
                        }
                    }
                });
            };

            initExpenses = function() {
                var expenseUrl = '/' + page + '/get?',
                    orderByGetList = [],
                    filterGetList = [];

                ko.utils.arrayForEach(self.orderBy(), function(v) {
                    orderByGetList.push('orderBy=' + encodeURIComponent(JSON.stringify(v)));
                });

                ko.utils.arrayForEach(self.filter(), function(v) {
                    orderByGetList.push('filter=' + encodeURIComponent(JSON.stringify(v)));
                });

                expenseUrl += orderByGetList.join('&');
                expenseUrl += filterGetList.join('&');

                $.getJSON(expenseUrl, function(data) {
                    var list = [],
                        newExpense;
                    ko.utils.arrayForEach(data.data, function(item) {
                        var obs;
                        obs = getItemObservable(item, page, self.expenses, preExpensesObservableFn, postExpensesObservableFn);
                        list.push(obs);
                    });
                    newExpense = getItemObservable({id: -1, value: '', note: '', date: '', category_id: null}, page, self.expenses, preExpensesObservableFn, postExpensesObservableFn);
                    list.push(newExpense);
                    self.expenses(list);
                });
            };

            initCategories = function() {
                $.getJSON('/category/get', function(data) {
                    var list = [],
                        nullCategory = {id: null, name: categoryTranslate, color: 'inherit', isDark: null};

                    list.push(nullCategory);
                    self.categoriesById[null] = nullCategory;
                    ko.utils.arrayForEach(data.data, function(category) {
                        var tc = tinycolor(category.color);
                        category.isDark = tc.isDark();
                        list.push(category);
                        self.categoriesById[category.id] = category;
                    });
                    self.categories(list);
                    initExpenses();
                });
            };

            initCategories();
        };

        expenseModel = new ExpenseModel();
        window.debug_expenseModel = expenseModel;
        ko.applyBindings(expenseModel);
    }

    if ('summary' === page) {
        SummaryModel = function() {
            var self = this,
                formatCurrencyForRows, addObservables, init;

            self.categoriesById = {};
            self.categoriesOrder = ko.observableArray();
            self.summaryAllYears = ko.observableArray();
            self.summaryPerYear = ko.observable({});

            self.toggleYear = function(yearRow) {
                var year = yearRow.year;
                if(yearRow.showMonth()) {
                    yearRow.showMonth(false);
                } else {
                    yearRow.showMonth(true);
                    if(undefined === self.summaryPerYear()[year]) {
                        $.getJSON('/' + page + '/get/' + year, function(data) {
                            var tmp = self.summaryPerYear();
                            formatCurrencyForRows(data.summary);
                            tmp[year] = data.summary;
                            self.summaryPerYear(tmp);
                        });
                    }
                }
            };

            self.filterMonth = function(sumCell) {
                var first = new Date(sumCell.year, sumCell.month -1, 1),
                    firstIso = $.datepicker.formatDate('yy-mm-dd', first),
                    last = getLastOfMonth(first),
                    lastIso = $.datepicker.formatDate('yy-mm-dd', last),
                    filter = [
                        ['date', '>=', firstIso],
                        ['date', '<=', lastIso]
                    ];

                location.href = 'expense.html#?filter:' + encodeURIComponent(JSON.stringify(filter)) + '?';
            };

            formatCurrencyForRows = function(rows) {
                ko.utils.arrayForEach(rows, function(row) {
                    ko.utils.objectForEach(row, function(k, v) {
                        if(0 === k.indexOf('value_')) {
                            row['locale_' + k] = formatCurrencyValue(v);
                        }
                    });
                });
            };

            addObservables = function(summary) {
                ko.utils.arrayForEach(summary, function(row) {
                    row.showMonth = ko.observable(false);
                });
            };

            init = function() {
                $.getJSON('/' + page + '/get', function(data) {
                    formatCurrencyForRows(data.summary);
                    addObservables(data.summary);
                    ko.utils.objectForEach(data.categories_dict, function (k, v) {
                        var tc = tinycolor(v.color);
                        v.isDark = tc.isDark();
                    });
                    self.categoriesById = data.categories_dict;
                    self.categoriesOrder(data.category_ids);
                    self.summaryAllYears(data.summary);
                });
            };

            init();
        };

        summaryModel = new SummaryModel();
        window.debug_summaryModel = summaryModel;
        ko.applyBindings(summaryModel);
    }

    if ('update' === page) {
        $('button.updates_check').on('click', function(x) {
            $.ajax({
                dataType: "json",
                url: '/update/check',
                method: 'PUT',
                success: function(data) {
                    window.console.log('data', data);
                    location.href += '';
                }
            });
        });

        $('button.updates_do').on('click', function(x) {
            $.ajax({
                dataType: "json",
                url: '/update/do',
                method: 'PUT',
                success: function(data) {
                    window.console.log('data', data);
                    location.href += '';
                }
            });
        });
    }

    if('undefined' !== typeof datepickerDateFormat) {
        $('.formatLocaleDate').each(function(k, v) {
            var el = $(v),
                parsedDate = $.datepicker.parseDate(el.attr('data-format'), el.text());

            el.text($.datepicker.formatDate(datepickerDateFormat, parsedDate));
        });
    }

    $('.notify').each(function(k, v) {
        var el = $(v);
        el.css({'transition-duration': '0.5s'});
        window.setInterval(function() {
            el.toggleClass('active');
        }, 1000);
        // debugger;
    });

    $('.formatLocaleCurrency').each(function(k, v) {
        var el = $(v),
            lv = formatCurrencyValue(el.text());

        el.text(lv);
    });
});
