
odoo.define('theme_britania.options', (require) => {
'use strict';

var core = require('web.core');
var qweb = core.qweb;

qweb.add_template('/theme_britania/static/src/xml/custom_options_menu.xml');

});