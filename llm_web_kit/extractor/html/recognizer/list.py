import json
import re
from typing import Any, List, Tuple

from lxml import html as lxml_html
from lxml.html import HtmlElement
from overrides import override

from llm_web_kit.exception.exception import HtmlListRecognizerException
from llm_web_kit.extractor.html.recognizer.recognizer import (
    BaseHTMLElementRecognizer, CCTag)
from llm_web_kit.libs.doc_element_type import DocElementType, ParagraphTextType
from llm_web_kit.libs.html_utils import (html_normalize_space, html_to_element,
                                         process_sub_sup_tags,
                                         replace_sub_sup_with_text_regex,
                                         restore_sub_sup_from_text_regex)
from llm_web_kit.libs.text_utils import normalize_text_segment

from .text import inline_tags


class ListAttribute():
    """列表属性."""
    UNORDERED = 'unordered'
    ORDERED = 'ordered'
    DEFINITION = 'definition'


class ListRecognizer(BaseHTMLElementRecognizer):
    """解析列表元素."""

    def to_content_list_node(self, base_url: str, parsed_content: HtmlElement, raw_html_segment: str) -> dict:
        """专化为列表元素的解析.

        Args:
            base_url:
            parsed_content:
            raw_html_segment:

        Returns:
        """
        if not isinstance(parsed_content, HtmlElement):
            raise HtmlListRecognizerException(f'parsed_content 必须是 HtmlElement 类型，而不是 {type(parsed_content)}')
        list_attribute, content_list, _, list_nest_level = self.__get_attribute(parsed_content)

        ele_node = {
            'type': DocElementType.LIST,
            'bbox': [],
            'content': {
                'items': content_list,
                'list_attribute': list_attribute,
                'list_nest_level': list_nest_level
            }
        }
        return ele_node

    @override
    def recognize(self, base_url: str, main_html_lst: List[Tuple[HtmlElement, HtmlElement]], raw_html: str, language:str = 'en') -> List[Tuple[HtmlElement, HtmlElement]]:
        """父类，解析列表元素.

        Args:
            base_url: str: 基础url
            main_html_lst: main_html在一层一层的识别过程中，被逐步分解成不同的元素
            raw_html: 原始完整的html

        Returns:
        """
        new_html_lst = []

        for html, raw_html in main_html_lst:
            if self.is_cc_html(html):
                new_html_lst.append((html, raw_html))
            else:
                lst = self._extract_list(html)
                new_html_lst.extend(lst)
        return new_html_lst

    def _extract_list(self, raw_html: HtmlElement) -> List[Tuple[HtmlElement, HtmlElement]]:
        """提取列表元素. 不支持嵌套列表，如果有嵌套的情况，则内部列表将作为一个单独的段落，内部列表的每个列表项作为一个单独的句子，使用句号结尾。
        列表在html中有以下几个标签：

        <ul>, <ol>, <dl>, <menu>, <dir>
        ol, dl是有序列表，ul, menu, dir是无序列表

        Args:
            raw_html:

        Returns:
            List[Tuple[str, str]]: 列表元素, 第一个str是<cc-list>xxx</cc-list>, 第二个str是原始的html内容
        """
        # tree = self._build_html_tree(raw_html)
        tree = raw_html
        self.__do_extract_list(tree)
        # 最后切割html
        # new_html = self._element_to_html(tree)
        new_html = tree
        lst = self.html_split_by_tags(new_html, CCTag.CC_LIST)
        return lst

    def __do_extract_list(self, root: HtmlElement) -> None:
        """提取列表元素.

        Args:
            root:

        Returns:
            Tuple[bool, list, str]: 第一个元素是是否有序; 第二个元素是个python list，内部是文本和行内公式，具体格式参考list的content_list定义。第三个元素是列表原始的html内容
        """
        list_tag_names = ['ul', 'ol', 'dl', 'menu', 'dir']

        if root.tag in list_tag_names:
            list_nest_level, list_attribute, content_list, raw_html, tail_text = self.__extract_list_element(root)
            text = json.dumps(content_list, ensure_ascii=False, indent=4)
            cc_element = self._build_cc_element(CCTag.CC_LIST, text, tail_text, list_attribute=list_attribute, list_nest_level=list_nest_level, html=raw_html)
            self._replace_element(root, cc_element)  # cc_element 替换掉原来的列表元素
            return

        for child in root.iterchildren():
            self.__do_extract_list(child)

    def __extract_list_item_text(self, child: HtmlElement) -> str:
        """提取列表项的文本内容.

        Args:
            element: 列表项HTML元素
        """
        text_paragraph = []

        def __extract_list_item_text_recusive(el: HtmlElement):
            list_container_tags = ('ul', 'ol', 'dl', 'menu', 'dir')
            is_sub_sup = el.tag == 'sub' or el.tag == 'sup'
            paragraph = []
            result = {}

            if el.tag == CCTag.CC_MATH_INLINE and el.text and el.text.strip():
                paragraph.append({'c': f'${el.text}$', 't': ParagraphTextType.EQUATION_INLINE})
            elif el.tag == CCTag.CC_CODE_INLINE and el.text and el.text.strip():
                paragraph.append({'c': f'`{el.text}`', 't': ParagraphTextType.CODE_INLINE})
            elif el.tag == 'br':
                paragraph.append({'c': '$br$', 't': ParagraphTextType.TEXT})
            elif el.tag == 'sub' or el.tag == 'sup':
                # 处理sub和sup标签，转换为GitHub Flavored Markdown格式
                current_text = ''
                if len(paragraph) > 0 and paragraph[-1]['t'] == ParagraphTextType.TEXT:
                    current_text = paragraph[-1]['c']
                    paragraph.pop()
                processed_text = process_sub_sup_tags(el, current_text, recursive=False)
                if processed_text:
                    paragraph.append({'c': processed_text, 't': ParagraphTextType.TEXT})
            elif el.tag in list_container_tags:
                list_attribute = self.__get_list_attribute(el)
                child_list = {
                    'list_attribute': list_attribute,
                    'items': []
                }
                for child in el.getchildren():
                    child_item = __extract_list_item_text_recusive(child)
                    if len(child_item) != 0:
                        child_list['items'].append(child_item)
                if child_list['items']:
                    result['child_list'] = child_list
            else:
                if el.text and el.text.strip():
                    _new_text = html_normalize_space(el.text.strip())
                    if len(el) == 0 and el.tag not in inline_tags:
                        _new_text += '$br$'
                    paragraph.append({'c': _new_text, 't': ParagraphTextType.TEXT})
                    el.text = None

                for child in el:
                    if child.tag not in inline_tags:
                        if paragraph:
                            paragraph[-1]['c'] += '$br$'

                    p = __extract_list_item_text_recusive(child)
                    if len(p) > 0:
                        # 如果子元素有child_list，需要保存
                        if 'child_list' in p:
                            result['child_list'] = p['child_list']
                        # 添加子元素的文本内容
                        if 'c' in p:
                            if p['c'] != '':
                                paragraph.append({'c': p['c'], 't': p.get('t', ParagraphTextType.TEXT)})
                    else:
                        if paragraph:
                            last_paragraph = paragraph[-1]['c']
                            if last_paragraph == '$br$':
                                del paragraph[-1]
                            else:
                                if last_paragraph.endswith('$br$'):
                                    paragraph[-1]['c'] = last_paragraph[:-4]

            if el.tag != 'li' and el.tail and el.tail.strip():
                _new_tail = html_normalize_space(el.tail.strip())
                if is_sub_sup:
                    # 如果尾部文本跟在sub/sup后面，直接附加到最后一个文本段落中
                    if len(paragraph) > 0 and paragraph[-1]['t'] == ParagraphTextType.TEXT:
                        paragraph[-1]['c'] += _new_tail
                else:
                    if len(paragraph) > 0 and el.tag not in inline_tags:
                        _new_tail = '$br$' + _new_tail
                    paragraph.append({'c': _new_tail, 't': ParagraphTextType.TEXT})

            if paragraph:
                # item['c'].strip(): 会导致前面处理br标签，添加的\n\n失效
                result['c'] = ' '.join(normalize_text_segment(item['c'].strip()) for item in paragraph)
            return result
        # list_item_tags = ('li', 'dd', 'dt', 'ul', 'div', 'p', 'span')
        # if child.tag in list_item_tags:
        # 去掉if限制条件，允许非标准结构的列表通过
        paragraph = __extract_list_item_text_recusive(child)
        if len(paragraph) > 0:
            tem_json = json.dumps(paragraph).replace('$br$\"}', '\"}')
            new_paragraph = json.loads(tem_json)
            text_paragraph.append(new_paragraph)

        for n, item in enumerate(text_paragraph):
            tem_json = json.dumps(item, ensure_ascii=False)
            tem_json = re.sub(r'(\s*\$br\$\s*)+', r'\\n', tem_json)
            text_paragraph[n] = json.loads(tem_json)

        return text_paragraph

    def __get_list_content_list(self, ele: HtmlElement, list_nest_level: int) -> list:
        """
        获取列表内容，将ul, ol, dl, menu, dir的子元素内容提取出来，形成列表
        Args:
            ele: 列表HTML元素
            list_nest_level: 列表嵌套层级

        Returns:
            list: 包含列表项内容的列表，即items
        """
        ele_html = lxml_html.tostring(ele, encoding='utf-8').decode()
        replace_tree_html = replace_sub_sup_with_text_regex(ele_html)
        ele = html_to_element(replace_tree_html)
        content_list = []
        # 处理根元素文本
        if ele.text and ele.text.strip():
            # 检查元素是否包含数学或代码相关属性
            text_content = html_normalize_space(ele.text.strip())
            root_item = {
                'c': text_content,
                't': ParagraphTextType.TEXT,
                'child_list': {}
            }
            content_list.append(root_item)
        for child in ele.iterchildren():
            text_paragraph = self.__extract_list_item_text(child)
            if len(text_paragraph) > 0:
                json_paragraph = restore_sub_sup_from_text_regex(json.dumps(text_paragraph))
                text_paragraph = json.loads(json_paragraph)
                content_list.extend(text_paragraph)
        return content_list

    def __extract_list_element(self, ele: HtmlElement) -> tuple[int, str, list, str, Any]:
        """提取列表元素，返回列表的属性，嵌套层级，内容列表，原始html，尾部文本."""
        list_attribute = self.__get_list_attribute(ele)
        list_nest_level = self.__get_list_type(ele)
        tail_text = ele.tail
        raw_html = self._element_to_html(ele)
        content_list = self.__get_list_content_list(ele, list_attribute)
        return list_nest_level, list_attribute, content_list, raw_html, tail_text

    def __get_list_attribute(self, list_ele: HtmlElement) -> str:
        """获取list的属性."""
        if list_ele.tag in ['dl']:
            return ListAttribute.DEFINITION
        elif list_ele.tag in ['ol']:
            return ListAttribute.ORDERED
        elif list_ele.tag in ['ul', 'menu', 'dir']:
            return ListAttribute.UNORDERED
        else:
            return ''

    def __get_list_type(self, list_ele: HtmlElement) -> int:
        """获取list嵌套的层级。

        计算一个列表元素的最大嵌套深度，通过递归遍历所有子元素。
        例如：
        - 没有嵌套的列表返回1
        - 有一层嵌套的列表返回2
        - 有两层嵌套的列表返回3

        Args:
            list_ele: 列表HTML元素

        Returns:
            int: 列表的最大嵌套深度
        """
        list_type = ['ul', 'ol', 'dl', 'menu', 'dir']

        def get_max_depth(element):
            max_child_depth = 0
            for child in element.iterchildren():
                if child.tag in list_type:
                    # 找到嵌套列表，其深度至少为1
                    child_depth = 1 + get_max_depth(child)
                    max_child_depth = max(max_child_depth, child_depth)
                else:
                    # 对非列表元素递归检查其子元素
                    child_depth = get_max_depth(child)
                    max_child_depth = max(max_child_depth, child_depth)
            return max_child_depth
        return get_max_depth(list_ele) + 1

    def __get_attribute(self, html: HtmlElement) -> Tuple[bool, dict, str]:
        """获取element的属性.

        Args:
            html:

        Returns:
            Tuple[str]: 第一个元素是是否有序; 第二个元素是个python list，内部是文本和行内公式，具体格式参考list的content_list定义。第三个元素是列表原始的html内容
        """
        # ele = self._build_html_tree(html)
        ele = html
        if ele is not None and ele.tag == CCTag.CC_LIST:
            list_attribute = ele.attrib.get('list_attribute', ListAttribute.UNORDERED)
            content_list = json.loads(ele.text)
            raw_html = ele.attrib.get('html')
            list_nest_level = ele.attrib.get('list_nest_level', 0)
            return list_attribute, content_list, raw_html, list_nest_level
        else:
            raise HtmlListRecognizerException(f'{html}中没有cclist标签')
