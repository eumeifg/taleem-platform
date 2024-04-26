(function(define) {
    'use strict';
    define([
        'jquery',
        'js/student_account/views/FormView'
    ],
        function($, FormView) {
            return FormView.extend({
                el: '#second-password-form',

                tpl: '#second_password-tpl',

                events: {
                    'click .js-second-password': 'submitForm'
                },

                formType: 'second-password',

                requiredStr: '',
                optionalStr: '',

                submitButton: '.js-second-password',

                preRender: function() {
                    this.element.show($(this.el));
                    this.element.show($(this.el).parent());
                    this.listenTo(this.model, 'sync', this.saveSuccess);
                },

                saveSuccess: function() {
                    this.trigger('second-password-verified');
                    this.stopListening();
                }
            });
        });
}).call(this, define || RequireJS.define);
