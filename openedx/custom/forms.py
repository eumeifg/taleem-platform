# -*- coding: UTF-8 -*-

from django import forms
from django.utils.safestring import mark_safe


class BootstrapModelForm(forms.ModelForm):
    def as_div(self):
        output = []
        for boundfield in self:
            row_template = u'''
            <div class="fieldset">
                %(label)s
                %(field)s
                %(error_text)s
            </div>
            '''
            row_dict = {
                "label" : boundfield.label_tag(),
                "field" : boundfield.as_widget(),
                "error_text" : "",
            }

            if boundfield.errors:
                row_dict["error_text"] = boundfield.errors

            output.append(row_template % row_dict)
        return mark_safe(u'\n'.join(output))
