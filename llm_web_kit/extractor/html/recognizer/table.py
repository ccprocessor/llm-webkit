import copy
import re
from typing import Any, List, Tuple

from lxml import html
from lxml.html import HtmlElement
from lxml.html.clean import Cleaner
from overrides import override

from llm_web_kit.exception.exception import HtmlTableRecognizerException
from llm_web_kit.extractor.html.recognizer.ccmath import MathRecognizer
from llm_web_kit.extractor.html.recognizer.recognizer import (
    BaseHTMLElementRecognizer, CCTag)
from llm_web_kit.libs.doc_element_type import DocElementType
from llm_web_kit.libs.html_utils import (element_to_html_unescaped,
                                         html_normalize_space, html_to_element,
                                         process_sub_sup_tags,
                                         replace_sub_sup_with_text_regex,
                                         restore_sub_sup_from_text_regex)
from llm_web_kit.libs.text_utils import normalize_text_segment

from .text import inline_tags

new_inline_tags = inline_tags.union({'table', 'tr', 'td', 'th', 'thead', 'tbody', 'tfoot', 'caption'})

allow_tags = ['table', 'tr', 'td', 'th', 'thead', 'tbody', 'tfoot', 'caption', 'sub', 'sup', 'ccmath-inline', 'ccmath-interline', 'cccode', 'cccode-inline']

cleaner = Cleaner(
    safe_attrs_only=False,
    page_structure=False,
    style=True,
    scripts=True,
    comments=True,
    links=False,
    meta=True,
    embedded=True,
    frames=True,
    forms=True,
    annoying_tags=True,
    allow_tags=allow_tags
)

# 空元素
VOID_ELEMENTS = {
    'area', 'base', 'br', 'col', 'embed', 'hr',
    'img', 'input', 'link', 'meta', 'param',
    'source', 'track', 'wbr'
}

KEEP_ATTRS = {'colspan', 'rowspan'}


def table_clean_attributes(element):
    attrs = list(element.attrib.keys())
    for attr in attrs:
        if attr not in KEEP_ATTRS:
            del element.attrib[attr]
    for child in element.iterchildren():
        table_clean_attributes(child)


class TableRecognizer(BaseHTMLElementRecognizer):
    """解析table元素."""

    def __init__(self):
        super().__init__()
        self.math_recognizer = MathRecognizer()

    @override
    def recognize(self,
                  base_url: str,
                  main_html_lst: List[Tuple[HtmlElement, HtmlElement]],
                  raw_html: str,
                  language:str = 'en') -> List[Tuple[HtmlElement, HtmlElement]]:
        """父类，解析表格元素.

        Args:
            base_url: str: 基础url
            main_html_lst: main_html在一层一层的识别过程中，被逐步分解成不同的元素
            raw_html: 原始完整的html

        Returns:
            List[Tuple[HtmlElement, HtmlElement]]: 处理后的HTML元素列表
        """
        final_result = list()
        for cc_html, o_html in main_html_lst:
            if self.__is_contain_cc_html(cc_html):
                final_result.append((cc_html, o_html))
            else:
                lst = self.__extract_tables(cc_html)
                final_result.extend(lst)
        return final_result

    @override
    def to_content_list_node(self, base_url: str, parsed_content: HtmlElement, raw_html_segment: str) -> dict:
        table_type, table_nest_level, table_body = self.__get_attribute(parsed_content)

        # 确保 table_body 不为 None 且是字符串类型
        html_content = table_body if table_body is not None else ''
        # 使用传入的 raw_html_segment 或将 parsed_content 转换为字符串
        if table_type:
            cc_table_type = DocElementType.COMPLEX_TABLE
        else:
            cc_table_type = DocElementType.SIMPLE_TABLE
        d = {
            'type': cc_table_type,
            'raw_content': raw_html_segment,
            'content': {
                'html': html_content,
                'is_complex': table_type,
                'table_nest_level': table_nest_level
            }
        }
        return d

    def __is_contain_cc_html(self, cc_html: HtmlElement) -> bool:
        """判断html片段是否是cc标签."""
        return BaseHTMLElementRecognizer.is_cc_html(cc_html)

    def __is_table_empty(self, table: HtmlElement) -> bool:
        """table是否为空."""
        # 合并单元格查询
        cells = table.xpath('.//td | .//th')
        for cell in cells:
            if cell.text and cell.text.strip():
                return False
            stack = [cell]
            while stack:
                elem = stack.pop()
                if elem.text and elem.text.strip():
                    return False
                if elem.tail and elem.tail.strip():
                    return False
                # 添加子元素到栈中(倒序保证处理顺序)
                stack.extend(reversed(elem.getchildren()))
        return True

    def __is_percentage(self, value: str) -> bool:
        """百分数判断."""
        if not value.endswith('%'):
            return False
        num_part = value.rstrip('%').strip()
        try:
            float(num_part)  # 检查%前面是否为有效数字
            return True
        except ValueError:
            return False

    def __is_simple_table(self, tree: HtmlElement) -> bool:
        """处理table元素，判断是是否复杂：是否包含合并单元格."""
        cells = tree.xpath('.//td | .//th')
        for cell in cells:
            colspan_str = cell.get('colspan', '1').strip('"\'\\,.:')
            rowspan_str = cell.get('rowspan', '1').strip('"\'\\,.:')
            # colspan和rowspan的值为百分数时设置为100，否则尝试转为整数，默认为1
            try:
                colspan = 100 if self.__is_percentage(colspan_str) else int(colspan_str or 1)
            except ValueError:
                colspan = 1
            try:
                rowspan = 100 if self.__is_percentage(rowspan_str) else int(rowspan_str or 1)
            except ValueError:
                rowspan = 1
            if (colspan > 1) or (rowspan > 1):
                return False
        return True

    def __is_table_nested(self, element: HtmlElement) -> int:
        """计算表格的嵌套层级."""
        if element.tag != 'table':
            return 0

        # 初始化栈结构：存储(当前元素, 当前层级)
        stack = [(element, 1)]
        max_level = 1

        # 深度优先遍历
        while stack:
            current, current_level = stack.pop()
            # 更新最大层级
            max_level = max(max_level, current_level)
            # 遍历子元素（倒序保证处理顺序）
            for child in reversed(current.getchildren()):
                if child.tag == 'table':
                    # 遇到子表格时层级+1
                    stack.append((child, current_level + 1))
                else:
                    # 非表格元素保持当前层级
                    stack.append((child, current_level))
        return max_level

    def __extract_tables(self, tree: HtmlElement) -> List[Tuple[HtmlElement, HtmlElement]]:
        """提取html中的table元素."""
        self.__do_extract_tables(tree)
        new_html = tree
        lst = self.html_split_by_tags(new_html, CCTag.CC_TABLE)
        return lst

    def __get_table_type(self, child: HtmlElement) -> str:
        """获取table的类型."""
        assert isinstance(child, HtmlElement)
        empty_flag = self.__is_table_empty(child)
        if empty_flag:
            return 'empty'
        level = self.__is_table_nested(child)
        # 是否跨行跨列
        flag = (level < 2 and self.__is_simple_table(child))
        if flag:
            table_type = 'simple'
        else:
            table_type = 'complex'
        return table_type

    def __check_table_include_math_code(self, raw_html: HtmlElement):
        """检查table中的内容，包括普通文本、数学公式和代码."""
        tem_raw_html = copy.deepcopy(raw_html)
        math_raw_html = self._element_to_html(tem_raw_html)
        math_res_parts = self.math_recognizer.recognize(
            base_url='',
            main_html_lst=[(tem_raw_html, tem_raw_html)],
            raw_html=math_raw_html
        )
        result = []
        if not math_res_parts:
            if tem_raw_html.tag == 'br' or tem_raw_html.xpath('.//br'):
                result.append("\n\n")
        for math_item in math_res_parts:
            ele_item = math_item[0]

            def process_node(node):
                """处理行内公式、行间公式、行间代码、行内代码."""
                if node.tag == CCTag.CC_MATH_INLINE:
                    if node.text and node.text.strip():
                        result.append(f'${node.text.strip()}$')
                    if node.tail and node.tail.strip():
                        result.append(node.tail.strip())
                # 处理行间公式
                elif node.tag == CCTag.CC_MATH_INTERLINE:
                    if node.text and node.text.strip():
                        result.append(f'$${node.text.strip()}$$')
                    if node.tail and node.tail.strip():
                        result.append(node.tail.strip())
                # 处理行间代码
                elif node.tag == CCTag.CC_CODE:
                    if node.text and node.text.strip():
                        result.append(f'```{node.text.strip()}```')
                    if node.tail and node.tail.strip():
                        result.append(node.tail.strip())
                # 处理行内代码
                elif node.tag == CCTag.CC_CODE_INLINE:
                    if node.text and node.text.strip():
                        result.append(f'`{node.text.strip()}`')
                    if node.tail and node.tail.strip():
                        result.append(node.tail.strip())
                elif node.tag in ['sub', 'sup']:
                    # 使用process_sub_sup_tags保留原始的sub/sup标签
                    processed_text = process_sub_sup_tags(node, '', lang='en', recursive=True)
                    if processed_text:
                        result.append(processed_text)
                    if node.tail and node.tail.strip():
                        result.append(node.tail.strip())
                else:
                    if node.tag == 'br' or node.tag not in new_inline_tags:
                        result.append('\n\n')

                    # 提取当前节点的文本
                    if node.text and node.text.strip():
                        cleaned_text = node.text.strip()
                        result.append(html_normalize_space(cleaned_text))

                    # 递归处理子节点
                    for child in node:
                        process_node(child)
                    # 处理节点的tail（元素闭合后的文本）
                    if node.tail and node.tail.strip():
                        if node.tag not in new_inline_tags:
                            result.append('\n\n')
                        cleaned_tail = node.tail.strip()
                        result.append(html_normalize_space(cleaned_tail))
            # 从根节点开始处理
            process_node(ele_item)
        return result

    def __simplify_td_th_content(self, table_nest_level, elem: HtmlElement) -> None:
        """简化 <td> 和 <th> 内容，保留嵌套表格结构."""
        if (elem.tag in ['td', 'th', 'table'] or
                any(child.tag in ['table', 'td', 'th'] for child in elem.iterchildren()) or
                elem.xpath('.//table') or elem.xpath('.//td') or elem.xpath('.//th')):
            if len(elem) > 0:
                # 需要继续遍历的情况
                for child in elem.iterchildren():
                    self.__simplify_td_th_content(table_nest_level, child)
            else:
                math_res = self.__check_table_include_math_code(elem)
                math_res_text = ' '.join(normalize_text_segment(item) for item in math_res)
                # 清除math和code元素
                if any(child.tag in [CCTag.CC_MATH_INLINE, CCTag.CC_MATH_INTERLINE, CCTag.CC_CODE, CCTag.CC_CODE_INLINE] for child in elem.iterchildren()):
                    elem.clear()
                elem.text = math_res_text
        else:
            math_res = self.__check_table_include_math_code(elem)
            elem.clear()
            if elem.tag not in new_inline_tags:
                math_res_text = ' '.join(normalize_text_segment(item) for item in math_res) + "\n\n"
            else:
                math_res_text = ' '.join(normalize_text_segment(item) for item in math_res)
            if elem.tag in VOID_ELEMENTS:
                elem_pre = elem.getprevious()
                if elem_pre is not None:
                    elem_pre.tail = math_res_text
                else:
                    elem_parent = elem.getparent()
                    if elem_parent is not None:
                        elem_parent_text = elem_parent.text + ' ' if elem_parent is not None and elem_parent.text is not None else ''
                        elem_parent.text = elem_parent_text + math_res_text
            else:
                elem.text = math_res_text

    def __get_table_body(self, table_type, table_nest_level, table_root):
        """获取并处理table body，返回处理后的HTML字符串。"""
        if table_type == 'empty':
            content = table_root.text_content()
            return content
        table_html = html.tostring(table_root, encoding='utf-8').decode()
        replace_tree_html = replace_sub_sup_with_text_regex(table_html)
        table_root = html_to_element(replace_tree_html)

        # 清理除了colspan和rowspan之外的属性
        self.__simplify_td_th_content(table_nest_level, table_root)
        table_clean_attributes(table_root)
        clean_html = cleaner.clean_html(self._element_to_html_entity(table_root))
        new_table_root = self._build_html_tree(clean_html)

        pattern = re.compile(r'(\s*\n\s*\n\s*|\n{2,})')
        for element in new_table_root.iter():
            # 清理元素前后的空白（不影响.text和.tail的内容）
            if element.text is not None:
                element.text = re.sub(pattern, '\n\n', element.text.strip())
            if element.tail is not None:
                element.tail = re.sub(pattern, '\n\n', element.tail.lstrip()).rstrip()

        tree_html = element_to_html_unescaped(new_table_root)
        restore_tree_html = restore_sub_sup_from_text_regex(tree_html)

        return restore_tree_html

    def __do_extract_tables(self, root: HtmlElement) -> None:
        """递归处理所有子标签."""
        if root.tag in ['table']:
            temp_tail = root.tail
            root.tail = None
            table_raw_html = self._element_to_html(root)
            table_type = self.__get_table_type(root)
            table_nest_level = self.__is_table_nested(root)
            tail_text = None
            table_body = self.__get_table_body(table_type, table_nest_level, root)
            cc_element = self._build_cc_element(
                CCTag.CC_TABLE, table_body, tail_text, table_type=table_type, table_nest_level=table_nest_level,
                html=table_raw_html)
            cc_element.tail = temp_tail
            self._replace_element(root, cc_element)
            return
        for child in root.iterchildren():
            self.__do_extract_tables(child)

    def __get_attribute(self, ele: HtmlElement) -> Tuple[bool, Any, Any]:
        """获取element的属性."""
        # ele = self._build_html_tree(html)
        if ele is not None and ele.tag == CCTag.CC_TABLE:
            table_type = ele.attrib.get('table_type')
            table_nest_level = ele.attrib.get('table_nest_level')
            table_flag = self.__get_content_list_table_type(table_type)
            table_body = ele.text
            return table_flag, table_nest_level, table_body
        else:
            raise HtmlTableRecognizerException(f'{ele}中没有cctable标签')

    def __get_content_list_table_type(self, table_type):
        """complex|simple 转为True|False."""
        is_complex = False
        if table_type == 'simple':
            is_complex = False
        elif table_type == 'complex':
            is_complex = True
        return is_complex
