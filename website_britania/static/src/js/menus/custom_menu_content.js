odoo.define('website_britania.custom_menu_content', function (require) {
    'use strict';
    var core = require('web.core');
    var editMenuDialog = require('website.contentMenu');
    var qweb = core.qweb;
    var _t = core._t;


    editMenuDialog.EditMenuDialog.include({
        
        _onEditMenuButtonClick: function (ev) {
            var $menu = $(ev.currentTarget).closest('[data-menu-id]');
            var menuID = $menu.data('menu-id');
            var menu = this.flat[menuID];
            if (menu) {
                var dialog = new weWidgetsMenuEntryDialog(this, {}, null, _.extend({
                    menuType: menu.fields['is_mega_menu'] ? 'mega' : undefined,
                }, menu.fields));
                dialog.on('save', this, link => {
                    _.extend(menu.fields, {
                        'name': link.text,
                        'url': link.url,
                        'desplegable': link.desplegable,
                        'is_mega_menu': link.desplegable,
                    });
                    $menu.find('.js_menu_label').first().text(menu.fields['name']);
                });
                dialog.open();
            } else {
                Dialog.alert(null, "Could not find menu entry");
            }
        },
        
        _onAddMenuButtonClick: function (ev) {
            var menuType = ev.currentTarget.dataset.type;
            var dialog = new weWidgetsMenuEntryDialog(this, {}, null, {
                menuType: menuType,
            });
            
            dialog.on('save', this, link => {
                var newMenu = {
                    'fields': {
                        'id': _.uniqueId('new-'),
                        'name': link.text,
                        'url': link.url,
                        'new_window': link.isNewWindow,
                        'is_mega_menu': link.desplegable, //menuType === 'mega',
                        'sequence': 0,
                        'parent_id': false,
                        'desplegable': link.desplegable,
                    },
                    'children': [],
                    'is_homepage': false,
                };
                this.flat[newMenu.fields['id']] = newMenu;
                this.$('.oe_menu_editor').append(
                    qweb.render('website.contentMenu.dialog.submenu', { submenu: newMenu })
                );
            });
            dialog.open();
        },
    });
    var weWidgetsMenuEntryDialog = editMenuDialog.MenuEntryDialog.extend({
    });
});