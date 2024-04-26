

import copy
import logging
import os
import re
import sys
import textwrap
from datetime import datetime

from pkg_resources import resource_string

import six
from django.conf import settings
from fs.errors import ResourceNotFound
from lxml import etree
from path import Path as path
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Boolean, List, Scope, String
from xmodule.contentstore.content import StaticContent
from xmodule.editing_module import EditingMixin
from xmodule.edxnotes_utils import edxnotes
from xmodule.html_checker import check_html
from xmodule.stringify import stringify_children
from xmodule.util.misc import escape_html_characters
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.x_module import (
    HTMLSnippet,
    ResourceTemplates,
    shim_xmodule_js,
    XModuleMixin,
    XModuleDescriptorToXBlockMixin,
    XModuleToXBlockMixin,
)
from xmodule.xml_module import XmlMixin, name_to_pathname

log = logging.getLogger("edx.courseware")

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


@edxnotes
@XBlock.needs("i18n")
class HtmlBlock(
    XmlMixin, EditingMixin,
    XModuleDescriptorToXBlockMixin, XModuleToXBlockMixin, HTMLSnippet, ResourceTemplates, XModuleMixin,
):
    """
    The HTML XBlock.
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        # it'd be nice to have a useful default but it screws up other things; so,
        # use display_name_with_default for those
        default=_("Text")
    )
    data = String(help=_("Html contents to display for this module"), default=u"", scope=Scope.content)
    source_code = String(
        help=_("Source code for LaTeX documents. This feature is not well-supported."),
        scope=Scope.settings
    )
    use_latex_compiler = Boolean(
        help=_("Enable LaTeX templates?"),
        default=False,
        scope=Scope.settings
    )
    editor = String(
        help=_(
            "Select Visual to enter content and have the editor automatically create the HTML. Select Raw to edit "
            "HTML directly. If you change this setting, you must save the component and then re-open it for editing."
        ),
        display_name=_("Editor"),
        default="raw",
        values=[
            {"display_name": _("Visual"), "value": "visual"},
            {"display_name": _("Raw"), "value": "raw"}
        ],
        scope=Scope.settings
    )

    ENABLE_HTML_XBLOCK_STUDENT_VIEW_DATA = 'ENABLE_HTML_XBLOCK_STUDENT_VIEW_DATA'

    @XBlock.supports("multi_device")
    def student_view(self, _context):
        """
        Return a fragment that contains the html for the student view
        """
        publish_completion_url = self.runtime.handler_url(self, 'publish_completion', '').rstrip('?')
        visual_completion = getattr(self, "visual_completion", None)
        done_state = getattr(self, "done", False)
        done_btn_state = 'disabled' if done_state else ''
        manual_completion = ''
        if visual_completion == 'manual':
            btn_text = "Marked as done" if done_state else "Mark as done"
            manual_completion = '''
            <div style="margin-top:10px; text-align: right;">
                <button class="mark-as-done btn btn-primary" data-completion-url="{completion_url}"
                    data-checked="{done}" {btn_state}>
                    {button_text}
                </button>
            </div>'''.format(
                completion_url=publish_completion_url,
                done='false',
                button_text=btn_text,
                btn_state=done_btn_state,
            )
            manual_completion += '''<script>
            $(".mark-as-done").click(function(){
                var el = $(this);
                var handlerUrl = $(this).data('completion-url');
                $.ajax({
                  type: 'POST',
                  url: handlerUrl,
                  data: JSON.stringify({
                    completion: 1.0,
                  }),
                }).then(
                  () => {
                    el.text("Marked as done");
                    el.prop("disabled", true);
                  },
                );

            });
            </script>'''

        fragment = Fragment(self.get_html() + manual_completion)
        add_webpack_to_fragment(fragment, 'HtmlBlockPreview')
        shim_xmodule_js(fragment, 'HTMLModule')
        return fragment

    @XBlock.supports("multi_device")
    def public_view(self, context):
        """
        Returns a fragment that contains the html for the preview view
        """
        return self.student_view(context)

    def student_view_data(self, context=None):  # pylint: disable=unused-argument
        """
        Return a JSON representation of the student_view of this XBlock.
        """
        if getattr(settings, 'FEATURES', {}).get(self.ENABLE_HTML_XBLOCK_STUDENT_VIEW_DATA, False):
            return {'enabled': True, 'html': self.get_html()}
        else:
            return {
                'enabled': False,
                'message': 'To enable, set FEATURES["{}"]'.format(self.ENABLE_HTML_XBLOCK_STUDENT_VIEW_DATA)
            }

    def get_html(self):
        """ Returns html required for rendering the block. """
        if self.data is not None and getattr(self.system, 'anonymous_student_id', None) is not None:
            return self.data.replace("%%USER_ID%%", self.system.anonymous_student_id)
        return self.data

    def studio_view(self, _context):
        """
        Return the studio view.
        """
        fragment = Fragment(
            self.system.render_template(self.mako_template, self.get_context())
        )
        add_webpack_to_fragment(fragment, 'HtmlBlockStudio')
        shim_xmodule_js(fragment, 'HTMLEditingDescriptor')
        return fragment

    preview_view_js = {
        'js': [
            resource_string(__name__, 'js/src/html/display.js'),
            resource_string(__name__, 'js/src/javascript_loader.js'),
            resource_string(__name__, 'js/src/collapsible.js'),
            resource_string(__name__, 'js/src/html/imageModal.js'),
            resource_string(__name__, 'js/common_static/js/vendor/draggabilly.js'),
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }
    preview_view_css = {'scss': [resource_string(__name__, 'css/html/display.scss')]}

    uses_xmodule_styles_setup = True
    requires_per_student_anonymous_id = True

    mako_template = "widgets/html-edit.html"
    resources_dir = None
    filename_extension = "xml"
    template_dir_name = "html"
    show_in_read_only_mode = True

    studio_view_js = {
        'js': [
            resource_string(__name__, 'js/src/html/edit.js')
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }
    studio_view_css = {
        'scss': [
            resource_string(__name__, 'css/editor/edit.scss'),
            resource_string(__name__, 'css/html/edit.scss')
        ]
    }

    # VS[compat] TODO (cpennington): Delete this method once all fall 2012 course
    # are being edited in the cms
    @classmethod
    def backcompat_paths(cls, filepath):
        """
        Get paths for html and xml files.
        """
        if filepath.endswith('.html.xml'):
            filepath = filepath[:-9] + '.html'  # backcompat--look for html instead of xml
        if filepath.endswith('.html.html'):
            filepath = filepath[:-5]  # some people like to include .html in filenames..
        candidates = []
        while os.sep in filepath:
            candidates.append(filepath)
            _, _, filepath = filepath.partition(os.sep)

        # also look for .html versions instead of .xml
        new_candidates = []
        for candidate in candidates:
            if candidate.endswith('.xml'):
                new_candidates.append(candidate[:-4] + '.html')
        return candidates + new_candidates

    @classmethod
    def filter_templates(cls, template, course):
        """
        Filter template that contains 'latex' from templates.

        Show them only if use_latex_compiler is set to True in
        course settings.
        """
        return 'latex' not in template['template_id'] or course.use_latex_compiler

    def get_context(self):
        """
        an override to add in specific rendering context, in this case we need to
        add in a base path to our c4x content addressing scheme
        """
        _context = EditingMixin.get_context(self)
        # Add some specific HTML rendering context when editing HTML modules where we pass
        # the root /c4x/ url for assets. This allows client-side substitutions to occur.
        _context.update({
            'base_asset_url': StaticContent.get_base_url_path_for_course_assets(self.location.course_key),
            'enable_latex_compiler': self.use_latex_compiler,
            'editor': self.editor
        })
        return _context

    # NOTE: html descriptors are special.  We do not want to parse and
    # export them ourselves, because that can break things (e.g. lxml
    # adds body tags when it exports, but they should just be html
    # snippets that will be included in the middle of pages.

    @classmethod
    def load_definition(cls, xml_object, system, location, id_generator):
        '''Load a descriptor from the specified xml_object:

        If there is a filename attribute, load it as a string, and
        log a warning if it is not parseable by etree.HTMLParser.

        If there is not a filename attribute, the definition is the body
        of the xml_object, without the root tag (do not want <html> in the
        middle of a page)

        Args:
            xml_object: an lxml.etree._Element containing the definition to load
            system: the modulestore system or runtime which caches data
            location: the usage id for the block--used to compute the filename if none in the xml_object
            id_generator: used by other impls of this method to generate the usage_id
        '''
        filename = xml_object.get('filename')
        if filename is None:
            definition_xml = copy.deepcopy(xml_object)
            cls.clean_metadata_from_xml(definition_xml)
            return {'data': stringify_children(definition_xml)}, []
        else:
            # html is special.  cls.filename_extension is 'xml', but
            # if 'filename' is in the definition, that means to load
            # from .html
            # 'filename' in html pointers is a relative path
            # (not same as 'html/blah.html' when the pointer is in a directory itself)
            pointer_path = "{category}/{url_path}".format(
                category='html',
                url_path=name_to_pathname(location.block_id)
            )
            base = path(pointer_path).dirname()
            # log.debug("base = {0}, base.dirname={1}, filename={2}".format(base, base.dirname(), filename))
            filepath = u"{base}/{name}.html".format(base=base, name=filename)
            # log.debug("looking for html file for {0} at {1}".format(location, filepath))

            # VS[compat]
            # TODO (cpennington): If the file doesn't exist at the right path,
            # give the class a chance to fix it up. The file will be written out
            # again in the correct format.  This should go away once the CMS is
            # online and has imported all current (fall 2012) courses from xml
            if not system.resources_fs.exists(filepath):

                candidates = cls.backcompat_paths(filepath)
                # log.debug("candidates = {0}".format(candidates))
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            try:
                with system.resources_fs.open(filepath, encoding='utf-8') as infile:
                    html = infile.read()
                    # Log a warning if we can't parse the file, but don't error
                    if not check_html(html) and len(html) > 0:
                        msg = "Couldn't parse html in {0}, content = {1}".format(filepath, html)
                        log.warning(msg)
                        system.error_tracker("Warning: " + msg)

                    definition = {'data': html}

                    # TODO (ichuang): remove this after migration
                    # for Fall 2012 LMS migration: keep filename (and unmangled filename)
                    definition['filename'] = [filepath, filename]

                    return definition, []

            except ResourceNotFound as err:
                msg = 'Unable to load file contents at path {0}: {1} '.format(
                    filepath, err)
                # add more info and re-raise
                six.reraise(Exception, Exception(msg), sys.exc_info()[2])

    @classmethod
    def parse_xml_new_runtime(cls, node, runtime, keys):
        """
        Parse XML in the new blockstore-based runtime. Since it doesn't yet
        support loading separate .html files, the HTML data is assumed to be in
        a CDATA child or otherwise just inline in the OLX.
        """
        block = runtime.construct_xblock_from_class(cls, keys)
        block.data = stringify_children(node)
        # Attributes become fields.
        for name, value in node.items():
            cls._set_field_if_present(block, name, value, {})
        return block

    # TODO (vshnayder): make export put things in the right places.

    def definition_to_xml(self, resource_fs):
        ''' Write <html filename="" [meta-attrs="..."]> to filename.xml, and the html
        string to filename.html.
        '''

        # Write html to file, return an empty tag
        pathname = name_to_pathname(self.url_name)
        filepath = u'{category}/{pathname}.html'.format(
            category=self.category,
            pathname=pathname
        )

        resource_fs.makedirs(os.path.dirname(filepath), recreate=True)
        with resource_fs.open(filepath, 'wb') as filestream:
            html_data = self.data.encode('utf-8')
            filestream.write(html_data)

        # write out the relative name
        relname = path(pathname).basename()

        elt = etree.Element('html')
        elt.set("filename", relname)
        return elt

    @property
    def non_editable_metadata_fields(self):
        """
        `use_latex_compiler` should not be editable in the Studio settings editor.
        """
        non_editable_fields = super(HtmlBlock, self).non_editable_metadata_fields
        non_editable_fields.append(HtmlBlock.use_latex_compiler)
        return non_editable_fields

    def index_dictionary(self):
        xblock_body = super(HtmlBlock, self).index_dictionary()
        # Removing script and style
        html_content = re.sub(
            re.compile(
                r"""
                    <script>.*?</script> |
                    <style>.*?</style>
                """,
                re.DOTALL |
                re.VERBOSE),
            "",
            self.data
        )
        html_content = escape_html_characters(html_content)
        html_body = {
            "html_content": html_content,
            "display_name": self.display_name,
        }
        if "content" in xblock_body:
            xblock_body["content"].update(html_body)
        else:
            xblock_body["content"] = html_body
        xblock_body["content_type"] = "Text"
        return xblock_body


class AboutFields(object):
    display_name = String(
        help=_("The display name for this component."),
        scope=Scope.settings,
        default="overview",
    )
    data = String(
        help=_("Html contents to display for this module"),
        default=u"",
        scope=Scope.content
    )


@XBlock.tag("detached")
class AboutBlock(AboutFields, HtmlBlock):
    """
    These pieces of course content are treated as HtmlBlocks but we need to overload where the templates are located
    in order to be able to create new ones
    """
    template_dir_name = "about"


class StaticTabFields(object):
    """
    The overrides for Static Tabs
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default="Empty",
    )
    course_staff_only = Boolean(
        display_name=_("Hide Page From Learners"),
        help=_("If you select this option, only course team members with"
               " the Staff or Admin role see this page."),
        default=False,
        scope=Scope.settings
    )
    data = String(
        default=textwrap.dedent(u"""\
            <p>Add the content you want students to see on this page.</p>
        """),
        scope=Scope.content,
        help=_("HTML for the additional pages")
    )


@XBlock.tag("detached")
class StaticTabBlock(StaticTabFields, HtmlBlock):
    """
    These pieces of course content are treated as HtmlBlocks but we need to overload where the templates are located
    in order to be able to create new ones
    """
    template_dir_name = None


class CourseInfoFields(object):
    """
    Field overrides
    """
    items = List(
        help=_("List of course update items"),
        default=[],
        scope=Scope.content
    )
    data = String(
        help=_("Html contents to display for this module"),
        default=u"<ol></ol>",
        scope=Scope.content
    )


@XBlock.tag("detached")
class CourseInfoBlock(CourseInfoFields, HtmlBlock):
    """
    These pieces of course content are treated as HtmlBlock but we need to overload where the templates are located
    in order to be able to create new ones
    """
    # statuses
    STATUS_VISIBLE = 'visible'
    STATUS_DELETED = 'deleted'
    TEMPLATE_DIR = 'courseware'

    template_dir_name = None

    def get_html(self):
        """ Returns html required for rendering XModule. """

        # When we switch this to an XBlock, we can merge this with student_view,
        # but for now the XModule mixin requires that this method be defined.
        if self.data != "":
            if self.system.anonymous_student_id:
                return self.data.replace("%%USER_ID%%", self.system.anonymous_student_id)
            return self.data
        else:
            # This should no longer be called on production now that we are using a separate updates page
            # and using a fragment HTML file - it will be called in tests until those are removed.
            course_updates = self.order_updates(self.items)
            context = {
                'visible_updates': course_updates[:3],
                'hidden_updates': course_updates[3:],
            }
            return self.system.render_template("{0}/course_updates.html".format(self.TEMPLATE_DIR), context)

    @classmethod
    def order_updates(self, updates):
        """
        Returns any course updates in reverse chronological order.
        """
        sorted_updates = [update for update in updates if update.get('status') == self.STATUS_VISIBLE]
        sorted_updates.sort(
            key=lambda item: (self.safe_parse_date(item['date']), item['id']),
            reverse=True
        )
        return sorted_updates

    @staticmethod
    def safe_parse_date(date):
        """
        Since this is used solely for ordering purposes, use today's date as a default
        """
        try:
            return datetime.strptime(date, '%B %d, %Y')
        except ValueError:  # occurs for ill-formatted date values
            return datetime.today()