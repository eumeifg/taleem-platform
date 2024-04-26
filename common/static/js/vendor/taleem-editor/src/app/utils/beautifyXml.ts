import { uniq } from 'lodash'

const beautify = require('js-beautify').html

export function beautifyXml (html) {
  const options = {
    indent_size: '2',
    unformatted: ['script'],
    indent_char: ' ',
    max_preserve_newlines: '-1',
    preserve_newlines: false,
    keep_array_indentation: false,
    break_chained_methods: false,
    indent_scripts: 'normal',
    brace_style: 'collapse',
    space_before_conditional: true,
    unescape_strings: false,
    jslint_happy: false,
    end_with_newline: false,
    wrap_line_length: '0',
    indent_inner_html: false,
    comma_first: false,
    e4x: false,
    indent_empty_lines: false,
  }
  let beautifiedXml = beautify(html, options)
  const tagsToClose = ['img', 'br']
  tagsToClose.forEach(tag => {
    const imgTags = beautifiedXml.match(new RegExp(`<${tag}(.*?)>`, 'gm'))
    if (imgTags) {
      uniq(imgTags).every(regexMatch => {
        if (!regexMatch.endsWith('/>')) {
          const regex = new RegExp('(<' + tag + '("[^"]*"|[^\/">])*)>', 'gi') // eslint-disable-line
          beautifiedXml = beautifiedXml.replace(regex, '$1/>')
          return false
        } else {
          return true
        }
      })
    }
  })
  beautifiedXml = beautifiedXml.replace(/[ \t]+(<script)/gm, '$1')
  return beautifiedXml
}
