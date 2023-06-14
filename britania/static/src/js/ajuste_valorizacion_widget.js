odoo.define("britania.ajusteValorizacionWidget", function(require){
    "use strict";

    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');

    var ajusteValorizacionWidget = Widget.extend({
        template: "britania.ajusteValorizacion",
        events: _.extend({}, Widget.prototype.events, {
            'click .mostrar-datos': '_onClickMostrarDatosButton',
        }),
        init: function (parent, params) {
            this.data = params.data;
            this._super(parent);
            console.log("INIT")
        },
        _onClickMostrarDatosButton: function(){
            let valores = {};
            let valores_originales = this.data.valuation_adjustment_lines;
            let encabezados = [];
            if (valores_originales){
                valores_originales.data.map( dato => {
                    if(dato.data.product_id){
                        if(_.has(valores,dato.data.product_id.data.display_name)){
                            let temporal = valores[dato.data.product_id.data.display_name];
                            let llave = dato.data.cost_line_id.data.display_name.toString();

                            if(_.has(temporal,llave)){

                                temporal[llave] += dato.data.additional_landed_cost;
                                
                            } else {

                                temporal[llave] = dato.data.additional_landed_cost;
                            }
                            if (encabezados.indexOf(llave) === -1) {
                                encabezados.push(llave);
                            }
                            temporal["total"] += dato.data.additional_landed_cost;
                        }else {
                            let vals = {producto: dato.data.product_id.data.display_name};
                            let llave = dato.data.cost_line_id.data.display_name.toString();
                            vals[llave] = dato.data.additional_landed_cost.toString();
                            if (encabezados.indexOf(llave) === -1) {
                                encabezados.push(llave);
                            }
                            vals["total"] = dato.data.additional_landed_cost;
                            valores[dato.data.product_id.data.display_name.toString()] = vals

                        }
                    }
                });
                console.log(valores);
            }
            console.log("Funciona")
        },
    });

    widget_registry.add('ajuste_valorizacion_widget', ajusteValorizacionWidget);

    return ajusteValorizacionWidget;

});