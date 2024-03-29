/** @odoo-module **/

import Dialog from 'web.Dialog';
import { qweb } from "web.core";
import { registry } from '@web/core/registry';
import { Many2OneField } from '@web/views/fields/many2one/many2one_field';
import { formatMonetary } from "@web/views/fields/formatters";
const { markup, onWillUpdateProps } = owl;
var myGlobalVar = 1;

export class AddOrderLineProductField extends Many2OneField {

    setup() {
        super.setup();

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.record.mode === 'edit' && nextProps.value) {
                if (!this.props.value ||
                    this.props.value[0] != nextProps.value[0]) {
                    // Field was updated if line was open in edit mode,
                    //      field is not emptied,
                    //      new value is different than existing value.
                    console.log("if will update")
                    this._onProductTemplateUpdate();
                }

            }
            else{
                 console.log("else");
                 window.history.go(0);
            }
        });
    }

    get configurationButtonHelp() {
        console.log("configurationButtonHelp")
        return this.env._t("Edit Configuration");
    }
    get isConfigurableTemplate() {
        console.log("isConfigurableTemplate",this.props.record)
        if(myGlobalVar == 2){
             window.history.go(0);
        }
        return this.props.record.data.is_configurable_product;
    }

    async _onProductTemplateUpdate() {
        console.log('_onProductTemplateUpdate', this.props.record)
        const result = await this.orm.call(
            'product.template',
            'get_single_product_variant',
            [this.props.record.data.product_ids[0]],
        );
        if(result && result.product_id) {
            if (this.props.record.data.product_id != result.product_id.id) {
                this.props.record.update({
                    // TODO right name get (same problem as configurator)
                    product_id: [result.product_id, 'whatever'],
                });
            }
        } else {
            this._openGridConfigurator(false);
        }
    }

    onEditConfiguration() {
        if (this.props.record.data.is_configurable_product) {
            this._openGridConfigurator(true);
        }
    }

    async _openGridConfigurator(edit) {
        const PurchaseOrderRecord_2 = this.props.record.model.root;
        // fetch matrix information from server;
        await PurchaseOrderRecord_2.update({
            grid_product_tmpl_id:this.props.record.data.product_ids[0],
        });
        let updatedLineAttributes = [];
        console.log("edit", edit)
        if (edit) {
            // provide attributes of edited line to automatically focus on matching cell in the matrix
            for (let ptnvav of this.props.record.data.product_no_variant_attribute_value_ids.records) {
                updatedLineAttributes.push(ptnvav.data.id);
            }
            for (let ptav of this.props.record.data.product_ids.records) {
                updatedLineAttributes.push(ptav.data.id);
            }
            updatedLineAttributes.sort((a, b) => { return a - b; });
        }


        this._openMatrixConfigurator(

            PurchaseOrderRecord_2.data.grid,
            this.props.record.data.product_ids[0],
            updatedLineAttributes,
        );

        if (!edit) {
            console.log('!edit')
            // remove new line used to open the matrix
//            PurchaseOrderRecord_2.data.order_line.removeRecord(this.props.record);
        }
    }

    _openMatrixConfigurator(jsonInfo, productTemplateId, editedCellAttributes) {
        console.log('_js', productTemplateId)
        const infos = JSON.parse(jsonInfo);
        const saleOrderRecord = this.props.record.model.root;
        const MatrixDialog = new Dialog(this, {
            title: this.env._t('Choose Product Variants'),
            size: 'extra-large', // adapt size depending on matrix size?
            $content: $(qweb.render(
                'product_matrix.matrix', {
                    header: infos.header,
                    rows: infos.matrix,
                    format({price, currency_id}) {
                        if (!price) { return ""; }
                        const sign = price < 0 ? '-' : '+';
                        const formatted = formatMonetary(
                            Math.abs(price),
                            {
                                currencyId: currency_id,
                            },
                        );
                        return markup(`${sign}&nbsp;${formatted}`);
                    }
                }
            )),
            buttons: [
                {text: this.env._t('Confirm'), classes: 'btn-primary', close: true, click: function (result) {
                    const $inputs = this.$('.o_matrix_input');
                    var matrixChanges = [];
                    _.each($inputs, function (matrixInput) {
                        if (matrixInput.value && matrixInput.value !== matrixInput.attributes.value.nodeValue) {
                            matrixChanges.push({
                                qty: parseFloat(matrixInput.value),
                                ptav_ids: matrixInput.attributes.ptav_ids.nodeValue.split(",").map(function (id) {
                                      return parseInt(id);
                                }),
                            });
                        }
                    });
                    if (matrixChanges.length > 0) {
                        // NB: server also removes current line opening the matrix
                        console.log("matrixChanges")
                        saleOrderRecord.update({
                            grid: JSON.stringify({changes: matrixChanges, product_template_id: productTemplateId}),
                            grid_update: true // to say that the changes to grid have to be applied to the SO.
                        });
                        myGlobalVar = 2;
                    }

                }
                },
                {text: this.env._t('Close'), close: true},
            ],
        }).open();

        MatrixDialog.opened(function () {
            MatrixDialog.$content.closest('.o_dialog_container').removeClass('d-none');
            if (editedCellAttributes.length > 0) {
                const str = editedCellAttributes.toString();
                MatrixDialog.$content.find('.o_matrix_input').filter((k, v) => v.attributes.ptav_ids.nodeValue === str)[0].focus();
            } else {
                MatrixDialog.$content.find('.o_matrix_input:first()').focus();
            }
        });
    }
}

AddOrderLineProductField.template = "add_product_line.AddProductField";

registry.category("fields").add("add_product_many2one", AddOrderLineProductField);
