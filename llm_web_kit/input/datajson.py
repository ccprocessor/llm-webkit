import copy
import json
from abc import ABC, abstractmethod
from typing import Dict, List

from overrides import override

from llm_web_kit.exception.exception import ExtractorChainInputException
from llm_web_kit.extractor.html.recognizer.list import ListAttribute
from llm_web_kit.libs.doc_element_type import DocElementType, ParagraphTextType
from llm_web_kit.libs.encode import sha256_hash
from llm_web_kit.libs.html_utils import (get_element_text, html_to_element,
                                         html_to_markdown_table,
                                         table_cells_count)
from llm_web_kit.libs.text_utils import normalize_math_delimiters


class DataJsonKey(object):
    """DataJson的键值key常量定义."""
    DATASET_NAME = 'dataset_name'
    FILE_FORMAT = 'data_source_category'
    CONTENT_LIST = 'content_list'
    METAINFO = 'meta_info'
    STATICS = 'statics'


class DataSourceCategory(object):
    """数据源类型常量定义.

    这是对我们将要处理的数据的一种分类：
    """
    HTML = 'HTML'
    CC = 'CC'
    LAB_CC = 'LAB_CC'
    EBOOK = 'EBOOK'
    PDF = 'PDF'
    # audio 和video目前没有做任何处理
    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'
    # txt和md基本是从网上直接下载的开源数据
    TXT = 'TXT'
    MD = 'MD'


class StructureMapper(ABC):
    """作用是把contentList结构组合转化为另外一个结构 例如，从contentList转化为html, txt, md等等.

    Args:
        object (_type_): _description_
    """

    def __init__(self):
        self.__txt_para_splitter = '\n'
        self.__md_para_splitter = ''
        self.__text_end = '\n'
        self.__list_item_start = '-'  # md里的列表项前缀
        self.__list_para_prefix = '  '  # 两个空格，md里的列表项非第一个段落的前缀：如果多个段落的情况，第二个以及之后的段落前缀
        self.__md_special_chars = ['#', '`']  # TODO 拼装table的时候还应该转义掉|符号
        self.__nodes_document_type = [DocElementType.MM_NODE_LIST, DocElementType.PARAGRAPH, DocElementType.LIST,
                                      DocElementType.SIMPLE_TABLE, DocElementType.COMPLEX_TABLE, DocElementType.TITLE,
                                      DocElementType.IMAGE, DocElementType.AUDIO, DocElementType.VIDEO,
                                      DocElementType.CODE, DocElementType.EQUATION_INTERLINE]
        self.__inline_types_document_type = [ParagraphTextType.EQUATION_INLINE, ParagraphTextType.CODE_INLINE]

    def to_html(self):
        raise NotImplementedError('This method must be implemented by the subclass.')

    def to_plain_md(self, exclude_nodes=DocElementType.EXCLUDE_PLAIN_MD_LIST,
                    exclude_inline_types=DocElementType.EXCLUDE_PLAIN_MD_INLINE_LIST, use_raw_image_url=False):
        """把content_list转化为md格式.

        Args:
            exclude_nodes (list): 需要排除的节点类型
            exclude_inline_types: 需要排除的内联类型
            use_raw_image_url: 是否使用原始img url
        Returns:
            str: md格式的文本内容
        """
        self.__validate_exclude_nodes(exclude_nodes, exclude_inline_types)
        md = self.__to_md(exclude_nodes, exclude_inline_types, use_raw_image_url)
        return md

    def to_txt(self, exclude_nodes=DocElementType.MM_NODE_LIST, exclude_inline_types=[]):
        """把content_list转化为txt格式.

        Args:
            exclude_nodes (list): 需要排除的节点类型
        Returns:
            str: txt格式的文本内容
        """
        text_blocks: list[str] = []  # 每个是个DocElementType规定的元素块之一转换成的文本
        content_lst = self._get_data()
        for page in content_lst:
            for content_lst_node in page:
                if content_lst_node['type'] not in exclude_nodes:
                    txt_content = self.__content_lst_node_2_txt(content_lst_node, exclude_inline_types)
                    if txt_content and len(txt_content) > 0:
                        text_blocks.append(txt_content)

        txt = self.__txt_para_splitter.join(text_blocks)
        txt = normalize_math_delimiters(txt)
        txt = txt.strip() + self.__text_end  # 加上结尾换行符
        return txt

    def __to_md(self, exclude_nodes=[], exclude_inline_types=[], use_raw_image_url=False):
        """把content_list转化为md格式.

        Args:
            exclude_nodes (list): 需要排除的节点类型
        Returns:
            str: md格式的文本内容
        """
        md_blocks = []  # 每个是个DocElementType规定的元素块之一转换成的文本
        content_lst = self._get_data()
        for page in content_lst:
            for content_lst_node in page:
                if content_lst_node['type'] not in exclude_nodes:
                    txt_content = self.__content_lst_node_2_md(content_lst_node, exclude_inline_types,
                                                               use_raw_image_url)
                    if len(md_blocks) > 0 and not txt_content.startswith("\n") and not md_blocks[-1].endswith("\n"):  # 若段落间没有换行，则添加换行
                        md_blocks.append("\n\n")
                    if txt_content and len(txt_content) > 0:
                        md_blocks.append(txt_content)

        md = self.__md_para_splitter.join(md_blocks)
        md = normalize_math_delimiters(md)
        md = md.strip() + self.__text_end  # 加上结尾换行符
        return md

    def __validate_exclude_nodes(self, exclude_nodes, exclude_inline_types):
        if isinstance(exclude_nodes, str):
            exclude_nodes = [exclude_nodes]
        if isinstance(exclude_inline_types, str):
            exclude_inline_types = [exclude_inline_types]
        if not isinstance(exclude_nodes, list):
            raise ExtractorChainInputException('exclude_nodes must be a list type.')
        if not isinstance(exclude_inline_types, list):
            raise ExtractorChainInputException('exclude_inline_types must be a list type.')
        for node in exclude_nodes:
            if node not in self.__nodes_document_type:
                raise ExtractorChainInputException(f'exclude_nodes contains invalid element type: {node}')
        for inline_type in exclude_inline_types:
            if inline_type not in self.__inline_types_document_type:
                raise ExtractorChainInputException(f'exclude_inline_types contains invalid inline type: {inline_type}')
        return exclude_nodes, exclude_inline_types

    def to_nlp_md(self, exclude_nodes=[], exclude_inline_types=[]):
        exclude_nodes, exclude_inline_types = self.__validate_exclude_nodes(exclude_nodes, exclude_inline_types)
        md = self.__to_md(exclude_nodes + DocElementType.MM_NODE_LIST, exclude_inline_types)
        return md

    def to_mm_md(self, exclude_nodes=[], exclude_inline_types=[], use_raw_image_url=False):
        self.__validate_exclude_nodes(exclude_nodes, exclude_inline_types)
        md = self.__to_md(exclude_nodes, exclude_inline_types, use_raw_image_url)
        return md

    def to_json(self, pretty=False) -> str:
        content_lst = self._get_data()
        if pretty:
            return json.dumps(content_lst, ensure_ascii=False, indent=4)
        else:
            return json.dumps(content_lst, ensure_ascii=False)

    def to_dict(self) -> list[dict]:
        return copy.deepcopy(self._get_data())

    @abstractmethod
    def _get_data(self) -> List[Dict]:
        raise NotImplementedError('This method must be implemented by the subclass.')

    def __process_nested_list(self, items, list_attribute, indent_level=0, exclude_inline_types=[]):
        """处理新格式的嵌套列表结构.

        Args:
            items: 列表项数组
            list_attribute: 列表属性（有序/无序/定义）
            indent_level: 缩进级别
            exclude_inline_types: 排除的内联类型

        Returns:
            list: 处理后的列表项段落
        """
        result = []

        # 设置缩进
        indent = '  ' * indent_level

        for item_idx, item in enumerate(items):
            # 根据列表属性确定前缀格式
            if list_attribute == ListAttribute.ORDERED:
                # 有序列表 - 使用数字编号
                list_prefix = f'{item_idx + 1}.'
            elif list_attribute == ListAttribute.DEFINITION:
                # 定义列表
                item_text = item.get('c', '')
                term_line = f'{item_text}'
                result.append(term_line)

                # 处理嵌套子列表，同样不添加特殊缩进
                child_list = item.get('child_list', {})
                if child_list and isinstance(child_list, dict) and 'items' in child_list:
                    child_items = child_list.get('items', [])
                    child_attribute = child_list.get('list_attribute', ListAttribute.UNORDERED)

                    if child_items:
                        # 传递原始缩进级别，不额外增加
                        child_result = self.__process_nested_list(
                            child_items,
                            child_attribute,
                            indent_level,  # 使用相同的缩进级别
                            exclude_inline_types
                        )
                        result.extend(child_result)
                continue
            else:
                # 无序列表 - 使用破折号
                list_prefix = self.__list_item_start
            if not isinstance(item, dict):
                # 尝试处理嵌套列表情况
                if isinstance(item, list):
                    # 如果是嵌套列表，转换为标准格式
                    if item and isinstance(item[0], list) and item[0] and isinstance(item[0][0], dict):
                        item = item[0][0]  # 取出实际的字典对象
                    else:
                        continue  # 跳过无法处理的情况
                else:
                    continue  # 如果不是dict也不是list，跳过该项

            item_text = item.get('c', '')

            # 创建列表项行
            item_line = f'{indent}{list_prefix} {item_text}'
            result.append(item_line)

            # 处理嵌套子列表
            child_list = item.get('child_list', {})
            if child_list and isinstance(child_list, dict) and 'items' in child_list:
                child_items = child_list.get('items', [])
                child_attribute = child_list.get('list_attribute', ListAttribute.UNORDERED)

                if child_items:
                    child_result = self.__process_nested_list(
                        child_items,
                        child_attribute,
                        indent_level + 1,
                        exclude_inline_types
                    )
                    result.extend(child_result)

        return result

    def __content_lst_node_2_md(self, content_lst_node: dict, exclude_inline_types: list = [],
                                use_raw_image_url=False) -> str:
        """把content_list里定义的每种元素块转化为markdown格式.

        Args:
            content_lst_node (dict): content_list里定义的每种元素块
        Returns:
            str: markdown格式
        """
        node_type = content_lst_node['type']
        if node_type == DocElementType.CODE:
            code = content_lst_node['content'][
                'code_content']  # 这里禁止有None的content, 如果有应该消灭在模块内部。模块应该处理更精细，防止因为拼装导致掩盖了错误。
            # 代码不可以 strip，因为首行可能有缩进，只能 rstrip
            code = code.rstrip()
            if not code:
                return ''
            language = content_lst_node['content'].get('language', '')
            if content_lst_node.get('inline', False):
                code = f'`{code}`'
            else:
                code = f'```{language}\n{code}\n```'
            return code
        elif node_type == DocElementType.EQUATION_INTERLINE:
            math_content = content_lst_node['content']['math_content']
            math_content = math_content.strip()
            math_content = f'$$\n{math_content}\n$$'
            return math_content
        elif node_type == DocElementType.IMAGE:
            image_path = content_lst_node['content'].get('path', '')
            image_data = content_lst_node['content'].get('data', '')
            image_alt = content_lst_node['content'].get('alt', '')
            image_title = content_lst_node['content'].get('title', '')
            image_caption = content_lst_node['content'].get('caption', [])
            image_url = content_lst_node['content'].get('url', '')
            image_footnote = content_lst_node['content'].get('footnote', [])
            if not image_path and not image_data:
                image_path = sha256_hash(image_url)

            if use_raw_image_url:
                image_path = image_url

            if image_alt:
                image_alt = image_alt.strip()
            else:
                image_alt = ''

            if image_title:
                image_title = image_title.strip()
            else:
                image_title = ''

            if len(image_caption) > 0:
                image_caption = image_caption[0].strip()
            else:
                image_caption = ''

            if len(image_footnote) > 0:
                image_footnote = image_footnote[0].strip()
            else:
                image_footnote = ''

            image_des = image_title if image_title else ''
            # 优先使用data, 其次path.其中data是base64编码的图片，path是图片的url
            if image_data:
                if image_des:
                    image = f'![{image_alt}]({image_data} "{image_des}")'
                else:
                    image = f'![{image_alt}]({image_data})'
            else:
                if image_des:
                    image = f'![{image_alt}]({image_path} "{image_des}")'
                else:
                    image = f'![{image_alt}]({image_path})'

            if image_caption:
                image_with_caption = f'{image}\n\n{image_caption}'
            else:
                image_with_caption = image

            if image_footnote:
                image_with_caption = f'{image_with_caption}\n\n{image_footnote}'

            return image_with_caption
        elif node_type == DocElementType.AUDIO:
            return ''  # TODO: 音频格式
        elif node_type == DocElementType.VIDEO:
            return ''  # TODO: 视频格式
        elif node_type == DocElementType.TITLE:
            title_content = content_lst_node['content']['title_content'].strip()
            if not title_content:
                return ''
            level = content_lst_node['content']['level']
            md_title_level = '#' * int(level)
            md_title = f'{md_title_level} {title_content}'
            return md_title
        elif node_type == DocElementType.PARAGRAPH:
            paragraph_el_lst = content_lst_node['content']
            one_para = self.__join_one_para(paragraph_el_lst, exclude_inline_types)
            return one_para
        elif node_type == DocElementType.LIST:
            list_content = content_lst_node['content']
            list_attribute = list_content.get('list_attribute', ListAttribute.UNORDERED)
            items = list_content.get('items', [])
            result = self.__process_nested_list(items, list_attribute, 0, exclude_inline_types)
            return '\n'.join(result)
        elif node_type == DocElementType.SIMPLE_TABLE:
            # 对文本格式来说，普通表格直接转为md表格，复杂表格返还原始html
            html_table = content_lst_node['content']['html']
            if html_table is not None:
                html_table = html_table.strip()
                cells_count = table_cells_count(html_table)
                if cells_count <= 1:  # 单个单元格的表格，直接返回文本
                    text = get_element_text(html_to_element(html_table)).strip()
                    return text
                md_table = html_to_markdown_table(html_table)
                return md_table
            else:
                return ''
        elif node_type == DocElementType.COMPLEX_TABLE:
            html_table = content_lst_node['content']['html']
            if html_table is not None:
                html_table = html_table.strip()
                return html_table
            else:
                return ''
        else:
            raise ValueError(f'content_lst_node contains invalid element type: {node_type}')  # TODO: 自定义异常

    def __escape_md_special_chars(self, txt: str) -> str:
        """转义markdown特殊字符.

        Args:
            txt (str): 需要转义的文本
        Returns:
            str: 转义后的文本
        """
        for char in self.__md_special_chars:
            txt = txt.replace(char, f'\\{char}')
        return txt

    def __para_2_md_list_item(self, paras_of_item: list, list_prefix: str) -> str:
        """把一个列表项的多个段落连接起来.

        Args:
            paras_of_item (list): 一个列表项的多个段落
            list_prefix (str): 列表项的前缀, 数字或者固定`-`字符串
        Returns:
            str: 连接后的字符串，如（只看第一个item， 写2个是为了举例)：
            - 段落1
              段落1的子段落1
              段落1的子段落2
            - 段落2
              段落2的子段落1
              段落2的子段落2
        """
        md_list_item = ''
        for i, para in enumerate(paras_of_item):
            if i == 0:
                md_list_item += f'{list_prefix} {para}'
            else:
                md_list_item += f'\n{self.__list_para_prefix} {para}'

        return md_list_item

    def __content_lst_node_2_txt(self, content_lst_node: dict, exclude_inline_types=[]) -> str:
        """把content_list里定义的每种元素块转化为纯文本格式.

        Args:
            content_lst_node (dict): content_list里定义的每种元素块
        Returns:
            str: 纯文本格式
        """
        node_type = content_lst_node['type']
        if node_type == DocElementType.CODE:
            code = content_lst_node['content']['code_content']
            code = (code or '').strip()
            language = content_lst_node['content'].get('language', '')
            if content_lst_node.get('inline', False):
                code = f'`{code}`'
            else:
                code = f'```{language}\n{code}\n```'
            return code
        elif node_type == DocElementType.EQUATION_INTERLINE:
            math_content = content_lst_node['content']['math_content']
            math_content = math_content.strip()
            math_content = f'$$\n{math_content}\n$$'
            return math_content
        elif node_type == DocElementType.IMAGE:
            image_path = content_lst_node['content'].get('path', '')
            image_data = content_lst_node['content'].get('data', '')
            image_alt = content_lst_node['content'].get('alt', '')
            image_title = content_lst_node['content'].get('title', '')
            image_caption = content_lst_node['content'].get('caption', '')

            if image_alt:
                image_alt = image_alt.strip()
            if image_title:
                image_title = image_title.strip()
            if image_caption:
                image_caption = image_caption.strip()

            image_des = image_title if image_title else image_caption if image_caption else ''
            # 优先使用data, 其次path.其中data是base64编码的图片，path是图片的url
            if image_data:
                image = f'![{image_alt}]({image_data} "{image_des}")'
            elif image_path:
                image = f'![{image_alt}]({image_path} "{image_des}")'
            else:
                image = f'![{image_alt}]({image_path} "{image_des}")'
            return image
        elif node_type == DocElementType.AUDIO:
            return ''
        elif node_type == DocElementType.VIDEO:
            return ''
        elif node_type == DocElementType.TITLE:
            title_content = content_lst_node['content']['title_content']
            title_content = (title_content or '').strip()
            return title_content
        elif node_type == DocElementType.PARAGRAPH:
            paragraph_el_lst = content_lst_node['content']
            one_para = self.__join_one_para(paragraph_el_lst, exclude_inline_types)
            return one_para
        elif node_type == DocElementType.LIST:
            list_content = content_lst_node['content']
            list_attribute = list_content.get('list_attribute', ListAttribute.UNORDERED)
            items = list_content.get('items', [])
            result = self.__process_nested_list(items, list_attribute, 0, exclude_inline_types)
            return '\n'.join(result)
        elif node_type == DocElementType.SIMPLE_TABLE:
            # 对文本格式来说，普通表格直接转为md表格，复杂表格返还原始html
            html_table = content_lst_node['content']['html']
            if html_table is not None:
                html_table = html_table.strip()
                md_table = html_to_markdown_table(html_table)
                return md_table
            else:
                return ''
        elif node_type == DocElementType.COMPLEX_TABLE:
            html_table = content_lst_node['content']['html']
            if html_table is not None:
                html_table = html_table.strip()
                return html_table
            else:
                return ''
        else:
            raise ValueError(f'content_lst_node contains invalid element type: {node_type}')

    def __join_one_para(self, para: list, exclude_inline_types: list = []) -> str:
        """把一个段落的元素块连接起来.

        Args:
            para (list): 一个段落的元素块
        Returns:
            str: 连接后的字符串
        """
        one_para = []
        for el in para:
            if el['t'] in exclude_inline_types:
                continue
            if el['t'] == ParagraphTextType.TEXT:
                c = el['c']
                if not c or not c.strip():
                    continue
                new_c = self.__escape_md_special_chars(c)  # 转义特殊字符
                one_para.append(new_c)
            elif el['t'] == ParagraphTextType.EQUATION_INLINE:
                one_para.append(f"${el['c'].strip()}$")
            elif el['t'] == ParagraphTextType.CODE_INLINE:
                one_para.append(f"`{el['c'].strip()}`")
            else:
                raise ValueError(f'paragraph_el_lst contains invalid element type: {el["t"]}')

        return ' '.join(one_para)


class StructureChecker(object):
    def _validate(self, json_obj: dict):
        """校验json_obj是否符合要求 如果不符合要求就抛出异常.

        Args:
            json_obj (dict): _description_
        """
        if not isinstance(json_obj, dict):
            raise ExtractorChainInputException('json_obj must be a dict type.')
        if DataJsonKey.CONTENT_LIST in json_obj:
            if not isinstance(json_obj.get(DataJsonKey.CONTENT_LIST, ''), list):
                raise ExtractorChainInputException('content_list must be a list type.')


class ContentList(StructureMapper):
    """content_list格式的工具链实现."""

    def __init__(self, json_data_lst: list):
        super().__init__()
        if json_data_lst is None:
            json_data_lst = []
        self.__content_list = json_data_lst

    def length(self) -> int:
        return len(self.__content_list)

    def append(self, content: dict):
        self.__content_list.append(content)

    def __getitem__(self, key):
        return self.__content_list[key]  # 提供读取功能

    def __setitem__(self, key, value):
        self.__content_list[key] = value  # 提供设置功能

    def __delitem__(self, key):
        del self.__content_list[key]

    @override
    def _get_data(self) -> List[Dict]:
        return self.__content_list


class DataJson(StructureChecker):
    """从json文件中读取数据."""

    def __init__(self, input_data: dict):
        """初始化DataJson对象，对象必须满足一定的格式，这里进行一些校验.

        Args:
            input_data (dict): _description_
        """
        copied_input = copy.deepcopy(input_data)  # 防止修改外部数据，同时也让修改这个变量必须通过函数方法
        self._validate(copied_input)
        self.__json_data = copied_input
        if DataJsonKey.CONTENT_LIST in copied_input:
            self.__json_data[DataJsonKey.CONTENT_LIST] = ContentList(copied_input[DataJsonKey.CONTENT_LIST])
        if DataJsonKey.CONTENT_LIST not in self.__json_data:
            self.__json_data[DataJsonKey.CONTENT_LIST] = ContentList([])

    def __getitem__(self, key):
        return self.__json_data[key]  # 提供读取功能

    def __setitem__(self, key, value):
        self.__json_data[key] = value  # 提供设置功能

    def __delitem__(self, key):
        del self.__json_data[key]

    def __contains__(self, key):
        return key in self.__json_data

    def get_dataset_name(self) -> str:
        return self.__json_data[DataJsonKey.DATASET_NAME]

    def get_file_format(self) -> str:
        return self.__json_data[DataJsonKey.FILE_FORMAT]

    def get_content_list(self) -> ContentList:
        cl = self.__json_data[DataJsonKey.CONTENT_LIST]
        return cl

    def get(self, key: str, default=None):
        return self.__json_data.get(key, default)

    def get_magic_html(self, page_layout_type=None):
        from llm_web_kit.extractor.html.extractor import HTMLPageLayoutType
        from llm_web_kit.libs.html_utils import extract_magic_html

        if page_layout_type is None:
            page_layout_type = HTMLPageLayoutType.LAYOUT_ARTICLE

        raw_html = self.get('html')
        base_url = self.get('url')

        return extract_magic_html(raw_html, base_url, page_layout_type)

    def to_json(self, pretty=False) -> str:
        """
        把datajson对象转化为json字符串， content_list对象作为json的content_list键值
        Args:
            pretty (bool): 是否格式化json字符串
        Returns:
            str: json字符串
        """
        json_dict = self.__json_data.copy()
        json_dict[DataJsonKey.CONTENT_LIST] = self.get_content_list().to_dict()
        if pretty:
            return json.dumps(json_dict, indent=2, ensure_ascii=False)
        return json.dumps(json_dict, ensure_ascii=False)

    def to_dict(self) -> dict:
        """
        把datajson对象转化为dict对象
        Returns:
            dict: dict对象
        """
        json_dict = self.__json_data.copy()
        json_dict[DataJsonKey.CONTENT_LIST] = self.get_content_list().to_dict()
        return json_dict
