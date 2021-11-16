odoo.define('website_britania.save_data_menu', (require) => {
    'use strict';
    let widgets = require('wysiwyg.widgets');

    widgets.LinkDialog.include({
        save: function() {
            let data = this._getData();
            if(data != null) {
                data.desplegable = this.$('input[name="desplegable"]').prop('checked') || false;
                this.data.desplegable = data.desplegable;
            }
            return this._super.apply(this,arguments);
        }
    });
});