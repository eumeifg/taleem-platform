/* global QuizMaker, _, XModule */
// no-useless-escape disabled because of warnings in regexp expressions within the
// "toXML" code. When the "useless escapes" were removed, some of the unit tests
// failed, but only in Jenkins, indicating browser-specific behavior.
/* eslint no-useless-escape: 0 */
/*jshint -W117 */

(function() {
    'use strict';
    var hasPropsHelper = {}.hasOwnProperty,
        extendsHelper = function(child, parent) {
            // This helper method was generated by CoffeeScript. Suppressing eslint warnings.
            var key;
            for (key in parent) { // eslint-disable-line no-restricted-syntax
                if (hasPropsHelper.call(parent, key)) {
                    child[key] = parent[key]; // eslint-disable-line no-param-reassign
                }
            }
            function ctor() {
                this.constructor = child;
            }

            ctor.prototype = parent.prototype;
            child.prototype = new ctor(); // eslint-disable-line no-param-reassign
            child.__super__ = parent.prototype; // eslint-disable-line no-param-reassign, no-underscore-dangle
            return child;
        };

    this.QuizMakerEditingDescriptor = (function(_super) {
        // The style of these declarations come from CoffeeScript. Rather than rewriting them,
        // the eslint warnings are being suppressed.
        extendsHelper(QuizMakerEditingDescriptor, _super); // eslint-disable-line no-use-before-define

        function QuizMakerEditingDescriptor(element) {
            var common_problem_tags = [
                'multiplechoiceresponse',
                'choiceresponse',
                'optionresponse',
                'numericalresponse',
                'stringresponse'
            ];
            var that = this,
                json_data = null,
                xml = '';
            this.onShowXMLButton = function() {
                return QuizMakerEditingDescriptor.prototype.onShowXMLButton.apply(that, arguments);
            };
            this.onToggleDirection = function() {
                return QuizMakerEditingDescriptor.prototype.onToggleDirection.apply(that, arguments);
            };

            this.element = element;
            if ($('.xml-box', this.element).length !== 0) {
                this.element.on('click', '.xml-tab', this.onShowXMLButton);
                xml = $('.xml-box', this.element)[0].value;
            }

            if (this.containCommonProblemTags(common_problem_tags, xml) && $('.markdown-box', this.element).length !== 0) {
                // We are showing "QuizMaker Editor" only for common problem types.
                // but showing "Advanced XML Editor" for Adnaved Problem Types only.
                json_data = TaleemEditor.QuizMaker.xmlToJSON(xml);
                this.createQuizMakerEditor(json_data);
            } else {
                this.createXMLEditor(xml);
                $(this.element.find('.editor-bar')).hide();
            }
            
            this.element.on('click', '.toggle-direction', this.onToggleDirection);
            $(this.element.find('.xml-box')).hide();
        }

        QuizMakerEditingDescriptor.prototype.containCommonProblemTags = function(common_problem_tags, xml) {
            return common_problem_tags.some(function(arrVal) {
                return xml.includes(arrVal);
              });
        };

        /*
         User has clicked to show the XML editor. Before XML editor is swapped in,
         the user will need to confirm the one-way conversion.
         */
         QuizMakerEditingDescriptor.prototype.onShowXMLButton = function(e) {
            e.preventDefault();
            if (this.confirmConversionToXml()) {
                var json_data = this.quiz_maker_editor.getValue();
                this.createXMLEditor(TaleemEditor.QuizMaker.toXML(json_data));
                this.xml_editor.setCursor(0);
                // Hide markdown-specific toolbar buttons
                $(this.element.find('.editor-bar')).hide();
            }
        };

        /*
         User has clicked to toggle UI controls direction.
         */
         QuizMakerEditingDescriptor.prototype.onToggleDirection = function(e) {
            e.preventDefault();
            if ($(".quiz-maker-editor").hasClass('quiz-maker-ltr')) {
                $(".quiz-maker-editor").removeClass('quiz-maker-ltr')
                $(".quiz-maker-editor").addClass("quiz-maker-rtl");
            } else {
                $(".quiz-maker-editor").removeClass('quiz-maker-rtl')
                $(".quiz-maker-editor").addClass("quiz-maker-ltr");    
            }
        };

        /*
         Creates the XML Editor and sets it as the current editor. If text is passed in,
         it will replace the text present in the HTML template.

         text: optional argument to override the text passed in via the HTML template
         */
         QuizMakerEditingDescriptor.prototype.createXMLEditor = function(text) {
            this.xml_editor = CodeMirror.fromTextArea($('.xml-box', this.element)[0], {
                mode: 'xml',
                lineNumbers: true,
                lineWrapping: true
            });
            if (text) {
                this.xml_editor.setValue(text);
            }

            this.setCurrentEditor(this.xml_editor);
            $(this.xml_editor.getWrapperElement()).toggleClass('CodeMirror-advanced');
            // Need to refresh to get line numbers to display properly.
            $(this.element.find('.quiz-maker-editor')).hide();
            // $(this.element.find('.modal-actions')).show();
            this.xml_editor.refresh();
        };

        /*
         Creates the Taleem custom editor (QuizMaker) and sets it as the current editor.
         */
        QuizMakerEditingDescriptor.prototype.createQuizMakerEditor = function(data) {
            this.quiz_maker_editor = new TaleemEditor.QuizMaker({ 
                shadowDom: true,
                ui: {
                    showHints:              true,
                    showScripts:            false,
                    showDeleteBtn:          false,
                    showDuplicateBtn:       false,
                    showAddQuestionBtn:     false,
                    showQuestionTypeSelect: false,
                    showSubmitBtn:          false,
                    showCancelBtn:          false,
                    question: {
                        showAddNewQuestionBtn:  false,
                        showAddHintBtn:         false,
                        showDuplicateBtn:       false,
                        showQuestionTypeSelect: false,
                    }
                },
                config: {
                    checkboxes: {
                        explanation:        true,
                        customScript:       false,
                        optionHints:        true,
                        compoundFeedback:   false,
                        partialCredit:      false
                    },
                    dropdown: {
                        optionHints: true,
                    },
                    'multi-choice': {
                        optionHints: true,
                    },
                    'numerical-input': {
                        tolerance: false,
                        trailingText: false,
                        partialCredit: false,
                    },
                    'text-input': {
                        feedback: false,
                        trailingText: false,
                    },
                },
            });

            this.setCurrentEditor(this.quiz_maker_editor);
            if (data) {
                this.quiz_maker_editor.setQuestion(data);
            }
            this.quiz_maker_editor.mount('quiz-maker-editor');
            if (this.quiz_maker_editor.refresh) {
                this.quiz_maker_editor.refresh();
            }

            //TODO: We need to remove this call in later version of editor.
            this.updateShadowDom();
        };

        /*
         Update the styling of shadow dom elements inside QuizMaker.
         */
        QuizMakerEditingDescriptor.prototype.updateShadowDom = function() {
            var shadowDomElement = document.getElementById('quiz-maker-editor');
            var styleHooks = shadowDomElement.shadowRoot.getElementById('style-hook');
            if (styleHooks !== null) {
                styleHooks.innerHTML += '<style> div.q-select select { width: 300px !important; font-size: 14px; height: 25px; box-sizing: content-box; line-height: 15px; } </style>';
            }
        };

        /*
         Called when save is called. Listeners are unregistered because editing the block again will
         result in a new instance of the descriptor. Note that this is NOT the case for cancel--
         when cancel is called the instance of the descriptor is reused if edit is selected again.
         */
         QuizMakerEditingDescriptor.prototype.save = function() {
             if (this.current_editor === this.quiz_maker_editor && this.quiz_maker_editor.getValue() !== undefined) {
                var value = TaleemEditor.QuizMaker.toXML(this.quiz_maker_editor.getValue());
                return {
                    data: value,
                    metadata: {
                        markdown: JSON.stringify(this.quiz_maker_editor.getValue())
                    }
                };
            } else {
                return {
                    data: this.xml_editor.getValue(),
                    nullout: ['markdown']
                };
            }
        };

        /*
         User has clicked to show the Advanced QuizMaker editor.
         */
        QuizMakerEditingDescriptor.prototype.onShowQuizMakerButton = function(e) {
            e.preventDefault();
            if (this.confirmConversionToQuizMaker()) {
                this.createQuizMakerEditor();
            }
        };

        /*
         Have the user confirm the one-way conversion to XML.
         Returns true if the user clicked OK, else false.
         */
         QuizMakerEditingDescriptor.prototype.confirmConversionToXml = function() {
        return confirm(gettext('If you use the Advanced Editor, this problem will be converted to XML and you will not be able to return to the QuizMaker Editor Interface.\n\nProceed to the Advanced Editor and convert this problem to XML?')); // eslint-disable-line max-len, no-alert
        };

        /*
         Have the user confirm the one-way conversion to Advance QuizMaker.
         Returns true if the user clicked OK, else false.
         */
        QuizMakerEditingDescriptor.prototype.confirmConversionToQuizMaker = function() {
            return confirm(gettext('Do you really want to use the tal3eem "QuizMaker Editor" ?')); // eslint-disable-line max-len, no-alert
        };
        
        /*
         Stores the current editor and hides the one that is not displayed.
         */
        QuizMakerEditingDescriptor.prototype.setCurrentEditor = function(editor) {
            if (this.current_editor && !(this.current_editor instanceof TaleemEditor.QuizMaker)) {
                $(this.current_editor.getWrapperElement()).hide();
            }
            this.current_editor = editor;

            if (editor !== null && !(editor instanceof TaleemEditor.QuizMaker)) {
                $(this.current_editor.getWrapperElement()).show();
            }

            return $(this.current_editor).focus();
        };

        return QuizMakerEditingDescriptor;
    }(XModule.Descriptor));
}).call(this);