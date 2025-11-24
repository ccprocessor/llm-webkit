import re
from copy import deepcopy

from lxml.html import HtmlElement

from llm_web_kit.exception.exception import HtmlMathRecognizerException
from llm_web_kit.extractor.html.recognizer.cc_math.common import (CCMATH,
                                                                  MathType,
                                                                  text_strip)
from llm_web_kit.libs.html_utils import (build_cc_element,
                                         check_and_balance_delimiters,
                                         element_to_html, replace_element)


def modify_tree(cm: CCMATH, math_render: str, o_html: str, node: HtmlElement, parent: HtmlElement):
    try:
        annotation_tags = node.xpath('.//*[local-name()="annotation"][@encoding="application/x-tex"]')
        math_type = MathType.MATHML
        tag_math_type_list = cm.get_equation_type(o_html)
        if not tag_math_type_list:
            return
        new_tag = tag_math_type_list[0][0]
        math_type = tag_math_type_list[0][1]
        if len(annotation_tags) > 0:
            annotation_tag = annotation_tags[0]
            text = annotation_tag.text
            if parent:
                style_value = parent.get('style')
                if style_value:
                    normalized_style_value = style_value.lower().strip().replace(' ', '').replace(';', '')
                    if 'display: none' in normalized_style_value:
                        parent.style = ''
            text = cm.wrap_math_md(text)
            if text:
                new_span = build_cc_element(html_tag_name=new_tag, text=text, tail=text_strip(node.tail), type=math_type, by=math_render, html=o_html)
                replace_element(node, new_span)
        elif text_strip(node.get('alttext')):
            # Get the alttext attribute
            text = node.get('alttext')
            text = cm.wrap_math_md(text)
            if text:
                new_span = build_cc_element(html_tag_name=new_tag, text=text, tail=text_strip(node.tail), type=math_type, by=math_render, html=o_html)
                replace_element(node, new_span)
        else:
            # Try translating to LaTeX
            tmp_node = deepcopy(node)
            tmp_node.tail = None
            mathml = element_to_html(tmp_node)

            if 'xmlns:' in mathml or re.search(r'<\w+:', mathml):
                mathml = re.sub(r'xmlns:\w+="([^"]*)"', r'xmlns="\1"', mathml)  # remove any xmlns:prefix
                mathml = re.sub(r'<(\w+):', '<', mathml)  # remove any prefix:mi
                mathml = re.sub(r'</(\w+):', '</', mathml)  # remove any /prefix:mi
                mathml = re.sub(r'([^\s])\s+([^\s])', r'\1 \2', mathml)  # remove extra spaces

            latex = cm.mml_to_latex(mathml)
            # 处理未转义的%为\%
            if latex:
                latex = re.sub(r'(?<!\\)%', r'\\%', latex)
                latex = check_and_balance_delimiters(latex)
            text = cm.wrap_math_md(latex)
            if text:
                # Set the html of the new span tag to the text
                new_span = build_cc_element(html_tag_name=new_tag, text=text, tail=text_strip(node.tail), type=math_type, by=math_render, html=o_html)
                replace_element(node, new_span)
    except Exception as e:
        raise HtmlMathRecognizerException(f'Error processing math tag: {e}')


# if __name__ == '__main__':
    # html = '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>a</mi><mo>&#x2260;</mo><mn>0</mn></math>'
    # element = html_to_element(html)
    # cm = CCMATH()
    # modify_tree(cm, 'mathjax', html, element, element)
