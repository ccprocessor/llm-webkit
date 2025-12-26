import re
from urllib.parse import unquote

from lxml.html import HtmlElement

from llm_web_kit.exception.exception import HtmlMathRecognizerException
from llm_web_kit.extractor.html.recognizer.cc_math.common import (
    CCMATH, CCMATH_INLINE, CCMATH_INTERLINE, LATEX_IMAGE_CLASS_NAMES,
    LATEX_IMAGE_SRC_NAMES, MathType, text_strip)
from llm_web_kit.libs.html_utils import build_cc_element, replace_element


def modify_tree(cm: CCMATH, math_render: str, o_html: str, node: HtmlElement, parent: HtmlElement):
    """识别并处理img标签中的数学公式，将其转换为对应的数学标签。

    Args:
        cm: CCMATH实例
        math_render: 渲染器名称
        o_html: 原始HTML
        node: 当前处理的img节点
        parent: 父节点
    """
    try:

        # 判断img的公式是否为行间公式
        def is_display_mode(node, src_name):
            # # 1. 检查src中的参数
            # if src_name and '?' in src_name:
            #     try:
            #         query_params = parse_qs(src_name.split('?', 1)[1])
            #         # 检查常见参数: displaystyle, mode, display等
            #         if any(query_params.get(param, ['0'])[0] in ['1', 'true', 'display']
            #                for param in ['displaystyle', 'mode', 'display']):
            #             return True
            #     except Exception:
            #         pass

            # # 2. 检查样式和类
            # style = node.get('style', '')
            # if 'display:block' in style or 'margin:auto' in style:
            #     return True

            # 3. 检查alt文本是否以$$开头结尾
            alt_text = node.get('alt', '')
            if alt_text.startswith('$$') and alt_text.endswith('$$'):
                return True

            # 4. 检查图片尺寸
            width_str = node.get('width', '')
            # 提取数字部分，处理带单位的情况（如 "100px"）
            width_match = re.match(r'^(\d+)', width_str)
            if width_match and int(width_match.group(1)) > 100:
                return True

            # 5. 检查是否后面紧跟<br>标签
            next_sibling = node.getnext()
            if next_sibling is not None and next_sibling.tag.lower() == 'br':
                return True

            return False

        # 确定公式类型（行内或行间）
        src_name = node.get('src', '')
        math_type = MathType.LATEX

        class_name = node.get('class')
        if class_name and class_name in LATEX_IMAGE_CLASS_NAMES:
            text = node.get('alt')
            if text and text_strip(text):
                new_tag = CCMATH_INTERLINE if is_display_mode(node, src_name) else CCMATH_INLINE
                new_span = build_cc_element(
                    html_tag_name=new_tag,
                    text=cm.wrap_math_md(text),
                    tail=text_strip(node.tail),
                    type=math_type,
                    by=math_render,
                    html=o_html
                )
                replace_element(node, new_span)

        if class_name and 'x-ck12' in class_name:
            text = node.get('alt')
            if text and text_strip(text):
                text = unquote(text)
                text = cm.wrap_math_md(text)
                text = cm.wrap_math_space(text)
                new_tag = CCMATH_INTERLINE if is_display_mode(node, src_name) else CCMATH_INLINE
                new_span = build_cc_element(
                    html_tag_name=new_tag,
                    text=text,
                    tail=text_strip(node.tail),
                    type=math_type,
                    by=math_render,
                    html=o_html
                )
                replace_element(node, new_span)

        if src_name:
            if any(s in src_name for s in LATEX_IMAGE_SRC_NAMES):
                if any(src in src_name for src in ['latex.php', '/images/math/codecogs']):
                    text = node.get('alt')
                    if text and text_strip(text):
                        text = unquote(text)
                        text = cm.wrap_math_md(text)
                        text = cm.wrap_math_space(text)
                        new_tag = CCMATH_INTERLINE if is_display_mode(node, src_name) else CCMATH_INLINE
                        new_span = build_cc_element(
                            html_tag_name=new_tag,
                            text=text,
                            tail=text_strip(node.tail),
                            type=math_type,
                            by=math_render,
                            html=o_html
                        )
                        replace_element(node, new_span)
                else:
                    text = src_name.split('?')[1:]
                    text = '?'.join(text)
                    text = unquote(text)
                    text = cm.wrap_math_md(text)
                    text = cm.wrap_math_space(text)
                    new_tag = CCMATH_INTERLINE if is_display_mode(node, src_name) else CCMATH_INLINE
                    new_span = build_cc_element(
                        html_tag_name=new_tag,
                        text=text,
                        tail=text_strip(node.tail),
                        type=math_type,
                        by=math_render,
                        html=o_html
                    )
                    replace_element(node, new_span)

    except Exception as e:
        raise HtmlMathRecognizerException(f'Error processing img tag: {e}')
