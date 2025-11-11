import copy
import re
import uuid
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from lxml import etree, html
from selectolax.parser import HTMLParser

# 行内标签
inline_tags = {
    'map', 'optgroup', 'span', 'br', 'input', 'time', 'u', 'strong', 'textarea', 'small', 'sub',
    'samp', 'blink', 'b', 'code', 'nobr', 'strike', 'bdo', 'basefont', 'abbr', 'var', 'i', 'cccode-inline',
    'select', 's', 'pic', 'label', 'mark', 'object', 'ccmath-inline', 'svg',
    'button', 'a', 'font', 'dfn', 'sup', 'kbd', 'q', 'script', 'acronym', 'option', 'img', 'big', 'cite',
    'em', 'marked-tail', 'marked-text'
    # 'td', 'th', 'dd', 'dt', 'li'
}

# 表格内部可能包含的跟表格相关的标签
table_tags_set = {"caption", "colgroup", "col", "thead", "tbody", "tfoot", "tr", "td", "th"}

# 需要删除的标签
tags_to_remove = {
    'title',
    'head',
    'nav',
    'style',
    'script',
    'noscript',
    'link',
    'meta',
    'iframe',
    'frame',
}

# 需要保留的特殊标签（即使它们是行内标签）
EXCLUDED_TAGS = {'img', 'br', 'li', 'dt', 'dd', 'td', 'th'}

# 需要删除的属性名模式（独立单词）
ATTR_PATTERNS_TO_REMOVE = {
    'nav',  # 'footer', 'header',  # 独立单词
}

# 需要删除的属性名模式（特定前缀/后缀）
ATTR_SUFFIX_TO_REMOVE = {
    # '-nav', '_nav',
    # '-footer', '_footer',  # 有特例，可能dl列表一组最后一项添加了自定义footer属性，先注释
    # '-header', '_header',  # 有特例，可能自定义的header中有标题，先注释
}

# 自定义标签
tail_block_tag = 'cc-alg-uc-text'


def add_data_uids(dom: html.HtmlElement) -> None:
    """为DOM所有节点添加data-uid属性（递归所有子节点）"""
    for node in dom.iter():
        try:
            node.set('data-uid', str(uuid.uuid4()))
        except TypeError:
            pass


def remove_all_uids(dom: html.HtmlElement) -> None:
    """移除DOM中所有data-uid属性."""
    for node in dom.iter():
        if 'data-uid' in node.attrib:
            del node.attrib['data-uid']


def build_uid_map(dom: html.HtmlElement) -> Dict[str, html.HtmlElement]:
    """构建data-uid到节点的映射字典."""
    return {node.get('data-uid'): node for node in dom.iter() if node.get('data-uid')}


def judge_table_parent(table_element, node_list):
    for node in node_list:
        ancestor = node.getparent()
        while ancestor is not None:
            if ancestor is table_element:
                return True
            elif ancestor.tag == 'table':
                break
            ancestor = ancestor.getparent()
    return False


def is_data_table(table_element: html.HtmlElement) -> bool:
    """判断表格是否是数据表格而非布局表格."""
    # 检查当前表格（不包括内部嵌套表格）是否有 caption 标签
    caption_nodes = table_element.xpath('.//caption')
    if judge_table_parent(table_element, caption_nodes):
        return True

    # 检查当前表格（不包括内部嵌套表格）是否有 colgroup 或 col 标签
    col_nodes = table_element.xpath('.//col')
    colgroup_nodes = table_element.xpath('.//colgroup')
    if judge_table_parent(table_element, col_nodes) or judge_table_parent(table_element, colgroup_nodes):
        return True

    # 检查当前表格（不包括内部嵌套表格）单元格是否有 headers 属性
    cell_nodes = table_element.xpath(".//*[self::td or self::th][@headers]")
    if judge_table_parent(table_element, cell_nodes):
        return True

    # 检查是否有 role="table" 或 data-table 属性
    if table_element.get('role') == 'table' or table_element.get('data-table'):
        return True

    for node in table_element.iterdescendants():
        if node.tag in table_tags_set:
            continue
        if node.tag not in inline_tags:
            return False

    return True


def has_non_listitem_children(list_element):
    """检查列表元素是否包含非列表项的直接子节点.

    :param list_element: lxml元素对象 (ul, ol, dl)
    :return: True 如果存在非列表项的直接子节点，否则 False
    """

    # 根据列表类型确定允许的子元素标签
    if list_element.tag in ['ul', 'ol']:
        allowed_tags = {'li'}
    elif list_element.tag == 'dl':
        allowed_tags = {'dt', 'dd'}

    # 使用XPath直接查找是否存在不允许的直接子元素
    # 例如，对于<ul>，查找所有不是<li>的直接子元素
    # 对于<dl>，查找所有不是<dt>或<dd>的直接子元素
    exclude_conditions = " and ".join([f"name()!='{tag}'" for tag in allowed_tags])
    disallowed_children_xpath = f"./*[{exclude_conditions}]"

    if list_element.xpath(disallowed_children_xpath):
        return True

    # 检查是否存在非空白文本节点
    text_children = list_element.xpath("./text()")
    non_whitespace_text = any(text.strip() for text in text_children)

    return non_whitespace_text


def extract_paragraphs(processing_dom: html.HtmlElement, uid_map: Dict[str, html.HtmlElement],
                       include_parents: bool = True) -> List[Dict[str, str]]:
    """获取段落.

    content_type 字段：用于标识段落内容的类型，可能的值包括：

        'block_element'：独立的块级元素

        'inline_elements'：纯内联元素组合

        'unwrapped_text'：未包裹的纯文本内容

        'mixed'：混合内容（包含文本和内联元素）

    :param processing_dom:
    :param uid_map:
    :param include_parents:
    :return: 段落列表，每个段落包含html、content_type和_original_element字段
    """

    # 创建表格类型映射，记录每个表格是数据表格还是布局表格
    table_types = {}

    # 先分析所有表格的类型
    for table in processing_dom.xpath('.//table'):
        table_types[table.get('data-uid')] = is_data_table(table)

    # 创建列表类型映射，记录每个列表是内容列表还是布局列表
    list_types = {}

    def is_block_element(node) -> bool:
        """判断是否为块级元素."""
        def judge_special_case(node, expected_tags, types_map):
            ancestor = node
            while ancestor is not None and ancestor.tag not in expected_tags:
                ancestor = ancestor.getparent()

            if ancestor is not None:
                ancestor_uid = ancestor.get('data-uid')
                if types_map.get(ancestor_uid, False):
                    # 数据表格/内容列表的子元素不作为块级元素
                    return False
                else:
                    # 布局表格/列表的子元素作为块级元素
                    return True

        # 处理表格和列表的特殊情况
        if node.tag in ('td', 'th'):
            return judge_special_case(node, ['table'], table_types)

        if node.tag == "li":
            return judge_special_case(node, ['ul', 'ol'], list_types)

        if node.tag == "dt" or node.tag == "dd":
            return judge_special_case(node, ['dl'], list_types)

        # 默认处理其他元素
        if node.tag in inline_tags:
            return False
        return isinstance(node, html.HtmlElement)

    def has_block_descendants(node):
        for child in node.iterdescendants():
            if is_block_element(child):
                if node.tag in inline_tags:
                    original_element = uid_map.get(node.get('data-uid'))
                    original_element.set('cc-block-type', "true")
                return True
        return False

    def is_content_list(list_element):
        # 获取列表项（支持多种列表类型）
        items = list_element.xpath("li | dt | dd")

        # 不包含列表项，则不是内容列表
        if len(items) == 0:
            return False
        # 列表包含非列表项子元素视为布局列表
        if has_non_listitem_children(list_element):
            return False

        # 列表内任意子项存在块级元素，则视为布局列表
        for item in items:
            if has_block_descendants(item):
                return False

        # 默认视为内容列表
        return True

    # 先分析所有列表的类型
    for list_element in processing_dom.xpath('.//ul | .//ol | .//dl'):
        list_types[list_element.get('data-uid')] = is_content_list(list_element)

    def clone_structure(path: List[html.HtmlElement]) -> Tuple[html.HtmlElement, html.HtmlElement]:
        """克隆节点结构."""
        if not path:
            raise ValueError('Path cannot be empty')
        if not include_parents:
            last_node = html.Element(path[-1].tag, **path[-1].attrib)
            return last_node, last_node
        root = html.Element(path[0].tag, **path[0].attrib)
        current = root
        for node in path[1:-1]:
            new_node = html.Element(node.tag, **node.attrib)
            current.append(new_node)
            current = new_node
        last_node = html.Element(path[-1].tag, **path[-1].attrib)
        current.append(last_node)
        return root, last_node

    paragraphs = []

    def process_node(node: html.HtmlElement, path: List[html.HtmlElement]):
        """递归处理节点."""
        current_path = path + [node]
        inline_content = []
        content_sources = []

        # 处理节点文本
        if node.text and node.text.strip():
            inline_content.append(('direct_text', node.text.strip()))
            content_sources.append('direct_text')

        # 处理子节点
        for child in node:
            if is_block_element(child) or has_block_descendants(child):
                # 处理累积的内联内容
                if inline_content:
                    try:
                        root, last_node = clone_structure(current_path)
                        merge_inline_content(last_node, inline_content)

                        content_type = 'mixed'
                        if all(t == 'direct_text' for t in content_sources):
                            content_type = 'unwrapped_text'
                        elif all(t == 'element' for t in content_sources):
                            content_type = 'inline_elements'

                        # 获取原始元素
                        original_element = uid_map.get(node.get('data-uid'))
                        paragraphs.append({
                            'html': etree.tostring(root, encoding='unicode').strip(),
                            'content_type': content_type,
                            '_original_element': original_element  # 添加原始元素引用
                        })
                    except ValueError:
                        pass
                    inline_content = []
                    content_sources = []

                # 处理块级元素
                if table_types.get(child.get('data-uid')) or (not has_block_descendants(child)):
                    try:
                        root, last_node = clone_structure(current_path + [child])
                        last_node.text = child.text if child.text else None
                        for grandchild in child:
                            last_node.append(copy.deepcopy(grandchild))

                        # 获取原始元素
                        original_element = uid_map.get(child.get('data-uid'))
                        paragraphs.append({
                            'html': etree.tostring(root, encoding='unicode').strip(),
                            'content_type': 'block_element',
                            '_original_element': original_element  # 添加原始元素引用
                        })
                    except ValueError:
                        pass
                else:
                    process_node(child, current_path)

                # 处理tail文本
                if child.tail and child.tail.strip():
                    inline_content.append(('tail_text', child.tail.strip()))
                    content_sources.append('tail_text')
            else:
                inline_content.append(('element', child))
                content_sources.append('element')
                if child.tail and child.tail.strip():
                    inline_content.append(('tail_text', child.tail.strip()))
                    content_sources.append('tail_text')

        # 处理剩余的内联内容
        if inline_content:
            try:
                root, last_node = clone_structure(current_path)
                merge_inline_content(last_node, inline_content)

                content_type = 'mixed'
                if all(t == 'direct_text' for t in content_sources):
                    content_type = 'unwrapped_text'
                elif all(t == 'element' for t in content_sources):
                    content_type = 'inline_elements'
                elif all(t in ('direct_text', 'tail_text') for t in content_sources):
                    content_type = 'unwrapped_text'

                # 获取原始元素
                original_element = uid_map.get(node.get('data-uid'))
                paragraphs.append({
                    'html': etree.tostring(root, encoding='unicode').strip(),
                    'content_type': content_type,
                    '_original_element': original_element  # 添加原始元素引用
                })
            except ValueError:
                pass

    def merge_inline_content(parent: html.HtmlElement, content_list: List[Tuple[str, str]]):
        """合并内联内容."""
        last_inserted = None
        for item_type, item in content_list:
            if item_type in ('direct_text', 'tail_text'):
                if last_inserted is None:
                    if not parent.text:
                        parent.text = item
                    else:
                        parent.text += ' ' + item
                else:
                    if last_inserted.tail is None:
                        last_inserted.tail = item
                    else:
                        last_inserted.tail += ' ' + item
            else:
                parent.append(copy.deepcopy(item))
                last_inserted = item

    # 开始处理
    process_node(processing_dom, [])

    # 去重
    seen = set()
    unique_paragraphs = []
    for p in paragraphs:
        if p['html'] not in seen:
            seen.add(p['html'])
            unique_paragraphs.append(p)

    return unique_paragraphs


def remove_xml_declaration(html_string):
    # 正则表达式匹配 <?xml ...?> 或 <?xml ...>（没有问号结尾的情况）
    pattern = r'<\?xml\s+.*?\??>'
    html_content = re.sub(pattern, '', html_string, flags=re.DOTALL)

    return html_content


def post_process_html(html_content: str) -> str:
    """对简化后的HTML进行后处理."""
    if not html_content:
        return html_content

    # 处理标签外的空白（保留标签内文本的换行）
    def replace_outside_tag_space(match):
        """只替换标签外的连续空白."""
        if match.group(1):  # 如果是标签内容
            return match.group(1)
        elif match.group(2):  # 如果是非标签内容
            # 将非标签内容中的连续空白替换为单个空格
            return re.sub(r'\s+', ' ', match.group(2))
        return match.group(0)  # 默认返回整个匹配

    # 使用正则匹配所有标签内容和非标签内容
    html_content = re.sub(r'(<[^>]+>)|([^<]+)', replace_outside_tag_space, html_content)

    return html_content.strip()


def remove_tags(dom):
    """删除特定的标签.

    :param dom:
    :return:
    """
    for tag in tags_to_remove:
        for node in dom.xpath(f'.//{tag}'):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)


def is_meaningful_content(element) -> bool:
    """严格判断元素是否包含有效内容."""
    if element.text and element.text.strip():
        return True
    if element.tag == 'img':
        src = element.get('src', '')
        return bool(src and src.strip())
    for child in element:
        if is_meaningful_content(child):
            return True
    if element.tail and element.tail.strip():
        return True
    return False


def clean_attributes(element):
    """清理元素属性，保留图片的有效src（排除base64）、alt，以及所有元素的class和id."""
    if element.tag == 'img':
        # 获取图片相关属性
        src = element.get('src', '').strip()
        alt = element.get('alt', '').strip()
        class_attr = element.get('class', '').strip()
        id_attr = element.get('id', '').strip()

        element.attrib.clear()  # 清除所有属性

        # 保留非base64的src
        if src and not src.startswith('data:image/'):
            element.set('src', src)
        # 保留alt（如果非空）
        if alt:
            element.set('alt', alt)
        # 保留class和id（如果非空）
        if class_attr:
            element.set('class', class_attr)
        if id_attr:
            element.set('id', id_attr)
    else:
        # 非图片元素：只保留class和id
        class_attr = element.get('class', '').strip()
        id_attr = element.get('id', '').strip()

        element.attrib.clear()  # 清除所有属性

        if class_attr:
            element.set('class', class_attr)
        if id_attr:
            element.set('id', id_attr)

    # 递归处理子元素
    for child in element:
        clean_attributes(child)


def remove_inline_tags(element):
    """递归移除所有指定的行内标签（包括嵌套情况），保留img和br等EXCLUDED_TAGS标签."""
    # 先处理子元素（深度优先）
    for child in list(element.iterchildren()):
        remove_inline_tags(child)

    # 如果当前元素是需要移除的行内标签
    if element.tag in inline_tags and element.tag not in EXCLUDED_TAGS:
        parent = element.getparent()
        if parent is None:
            return

        # 检查是否包含需要保留的标签（如img、br等）
        has_excluded_tags = any(
            child.tag in EXCLUDED_TAGS
            for child in element.iterdescendants()
        )

        # 如果包含需要保留的标签，则不移除当前元素
        if has_excluded_tags:
            return

        # 保存当前元素的各部分内容
        leading_text = element.text or ''  # 元素开始前的文本
        trailing_text = element.tail or ''  # 元素结束后的文本
        children = list(element)  # 子元素列表

        # 获取当前元素在父元素中的位置
        element_index = parent.index(element)

        # 1. 处理leading_text（元素开始前的文本）
        if leading_text:
            if element_index == 0:  # 如果是第一个子元素
                parent.text = (parent.text or '') + leading_text
            else:
                prev_sibling = parent[element_index - 1]
                prev_sibling.tail = (prev_sibling.tail or '') + leading_text

        # 2. 转移子元素到父元素中
        for child in reversed(children):
            parent.insert(element_index, child)

        # 3. 处理trailing_text（元素结束后的文本）
        if trailing_text:
            if len(children) > 0:  # 如果有子元素，追加到最后一个子元素的tail
                last_child = children[-1]
                last_child.tail = (last_child.tail or '') + trailing_text
            elif element_index == 0:  # 如果没有子元素且是第一个子元素
                parent.text = (parent.text or '') + trailing_text
            else:  # 如果没有子元素且不是第一个子元素
                prev_sibling = parent[element_index - 1] if element_index > 0 else None
                if prev_sibling is not None:
                    prev_sibling.tail = (prev_sibling.tail or '') + trailing_text
                else:
                    parent.text = (parent.text or '') + trailing_text

        # 4. 移除当前元素
        parent.remove(element)


def simplify_list(element):
    """简化列表元素，只保留第一组和最后一组（对于dl列表保留完整的dt+所有dd）"""
    if element.tag in ('ul', 'ol'):
        # 处理普通列表(ul/ol)
        items = list(element.iterchildren())
        if len(items) > 2:
            # 保留第一个和最后一个子元素
            for item in items[1:-1]:
                element.remove(item)

            # 在第一个和最后一个之间添加省略号
            ellipsis = etree.Element('span')
            ellipsis.text = '...'
            items[-1].addprevious(ellipsis)

    elif element.tag == 'dl':
        # 处理定义列表(dl)
        items = list(element.iterchildren())
        if len(items) > 2:
            # 找出所有dt元素
            dts = [item for item in items if item.tag == 'dt']

            if len(dts) > 1:
                # 获取第一组dt和所有后续dd
                first_dt_index = items.index(dts[0])
                next_dt_index = items.index(dts[1])
                first_group = items[first_dt_index:next_dt_index]

                # 获取最后一组dt和所有后续dd
                last_dt_index = items.index(dts[-1])
                last_group = items[last_dt_index:]

                # 清空dl元素
                for child in list(element.iterchildren()):
                    element.remove(child)

                # 添加第一组完整内容
                for item in first_group:
                    element.append(item)

                # 添加省略号
                ellipsis = etree.Element('span')
                ellipsis.text = '...'
                element.append(ellipsis)

                # 添加最后一组完整内容
                for item in last_group:
                    element.append(item)

    # 递归处理子元素
    for child in element:
        simplify_list(child)


def should_remove_element(element) -> bool:
    """判断元素的class或id属性是否匹配需要删除的模式."""

    class_name = element.get('class', '')
    id_name = element.get('id', '')

    if class_name in ATTR_PATTERNS_TO_REMOVE or id_name in ATTR_PATTERNS_TO_REMOVE:
        parent = element.getparent()
        if parent is not None and parent.tag == 'body':
            return True

    # 检查style属性
    style_attr = element.get('style', '')
    if style_attr:
        if 'display: none' in style_attr or 'display:none' in style_attr:
            return True

    return False


def remove_specific_elements(element):
    """删除class或id名匹配特定模式的标签及其内容."""
    for child in list(element.iterchildren()):
        remove_specific_elements(child)

    if should_remove_element(element):
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)


def truncate_text_content(element, max_length=500):
    """递归处理元素及其子元素的文本内容，总长度超过max_length时截断 但保持标签结构完整."""
    # 首先收集所有文本节点（包括text和tail）
    text_nodes = []

    # 收集元素的text
    if element.text and element.text.strip():
        text_nodes.append(('text', element, element.text))

    # 递归处理子元素
    for child in element:
        truncate_text_content(child, max_length)
        # 收集子元素的tail
        if child.tail and child.tail.strip():
            text_nodes.append(('tail', child, child.tail))

    # 计算当前元素下的总文本长度
    total_length = sum(len(text) for (typ, node, text) in text_nodes)

    # 如果总长度不超过限制，直接返回
    if total_length <= max_length:
        return

    # 否则进行截断处理
    remaining = max_length
    for typ, node, text in text_nodes:
        if remaining <= 0:
            # 已经达到限制，清空剩余的文本内容
            if typ == 'text':
                node.text = None
            else:
                node.tail = None
            continue

        if len(text) > remaining:
            # 需要截断这个文本节点
            if typ == 'text':
                node.text = text[:remaining] + '...'
            else:
                node.tail = text[:remaining] + '...'
            remaining = 0
        else:
            remaining -= len(text)


def process_paragraphs(paragraphs: List[Dict[str, str]], uid_map: Dict[str, html.HtmlElement]) -> Tuple[str, html.HtmlElement]:
    """处理段落并添加 _item_id，同时在原始DOM的对应元素上添加相同ID.

    Args:
        paragraphs: 段落列表，每个段落包含html、content_type和_original_element
        original_dom: 原始DOM树

    Returns:
        Tuple[简化后的HTML, 标记后的原始DOM]
    """
    result = []
    item_id = 1

    for para in paragraphs:
        try:
            root = html.fragment_fromstring(para['html'], create_parent=False)
            root_for_xpath = copy.deepcopy(root)
            content_type = para.get('content_type', 'block_element')

            # 公共处理步骤
            clean_attributes(root)
            simplify_list(root)
            # remove_inline_tags(root)

            # 跳过无意义内容
            if not is_meaningful_content(root):
                continue

            # 截断过长的文本内容
            truncate_text_content(root, max_length=1000)

            # 为当前段落和原始元素添加相同的 _item_id
            current_id = str(item_id)
            root.set('_item_id', current_id)

            # 对于非块级元素（inline_elements, unwrapped_text, mixed）
            original_parent = para['_original_element']  # 原网页中直接子元素的父节点
            if content_type != 'block_element':
                if original_parent is not None:
                    # root_for_xpath有子元素
                    original_element = uid_map.get(root_for_xpath.get('data-uid'))
                    if len(root_for_xpath) > 0:
                        if root_for_xpath.tag in inline_tags and original_element.tag != 'body' and original_element.get('cc-block-type') != "true":
                            original_element.set('_item_id', current_id)
                        else:
                            # 收集需要包裹的子元素
                            children_to_wrap = []
                            for child in root_for_xpath.iterchildren():
                                child_uid = child.get('data-uid')
                                if child_uid and child_uid in uid_map:
                                    original_child = uid_map[child_uid]
                                    children_to_wrap.append(original_child)

                            if children_to_wrap:
                                # 确定包裹范围
                                first_child = children_to_wrap[0]
                                last_child = children_to_wrap[-1]

                                # 获取在父节点中的位置
                                start_idx = original_parent.index(first_child)
                                end_idx = original_parent.index(last_child)

                                # 收集所有需要移动的节点
                                nodes_to_wrap = []
                                for i in range(start_idx, end_idx + 1):
                                    nodes_to_wrap.append(original_parent[i])

                                # 处理前面的文本
                                leading_text = original_parent.text if start_idx == 0 else original_parent[
                                    start_idx - 1].tail

                                # 处理后面的文本
                                # trailing_text = last_child.tail

                                # 创建wrapper元素
                                wrapper = etree.Element(tail_block_tag)
                                wrapper.set('_item_id', current_id)
                                # 如果父元素包含cc-select，那么包裹的wrapper元素也应该包含cc-select，避免_item_id和cc-select不在同一层级中
                                if original_parent.get("cc-select") is not None:
                                    wrapper.set("cc-select", original_parent.get("cc-select"))

                                # 设置前面的文本
                                if leading_text:
                                    wrapper.text = leading_text
                                    if start_idx == 0:
                                        original_parent.text = None
                                    else:
                                        original_parent[start_idx - 1].tail = None

                                # 移动节点到wrapper中
                                for node in nodes_to_wrap:
                                    original_parent.remove(node)
                                    wrapper.append(node)

                                # 插入wrapper
                                original_parent.insert(start_idx, wrapper)

                                # 设置后面的文本
                                # if trailing_text:
                                #     wrapper.tail = trailing_text
                                #     last_child.tail = None
                    else:
                        if content_type == 'inline_elements':
                            original_element.set('_item_id', current_id)
                        else:
                            # root_for_xpath只有文本内容
                            if root_for_xpath.text and root_for_xpath.text.strip():
                                # 1. 在原始DOM中查找匹配的文本节点
                                found = False

                                # 检查父节点的text
                                if original_parent.text and original_parent.text.strip() == root_for_xpath.text.strip():
                                    # 创建wrapper
                                    wrapper = etree.Element(tail_block_tag)
                                    wrapper.set('_item_id', current_id)
                                    wrapper.text = original_parent.text
                                    # 如果父元素包含cc-select，那么包裹的wrapper元素也应该包含cc-select
                                    if original_parent.get("cc-select") is not None:
                                        wrapper.set("cc-select", original_parent.get("cc-select"))
                                    # 替换父节点的text
                                    original_parent.text = None

                                    # 插入wrapper作为第一个子节点
                                    if len(original_parent) > 0:
                                        original_parent.insert(0, wrapper)
                                    else:
                                        original_parent.append(wrapper)

                                    found = True

                                # 检查子节点的tail
                                if not found:
                                    for child in original_parent.iterchildren():
                                        if child.tail and child.tail.strip() == root_for_xpath.text.strip():
                                            # 创建wrapper
                                            wrapper = etree.Element(tail_block_tag)
                                            wrapper.set('_item_id', current_id)
                                            wrapper.text = child.tail
                                            # 如果父元素包含cc-select，那么包裹的wrapper元素也应该包含cc-select
                                            if original_parent.get("cc-select") is not None:
                                                wrapper.set("cc-select", original_parent.get("cc-select"))
                                            # 替换tail
                                            child.tail = None

                                            # 插入wrapper到子节点之后
                                            parent = child.getparent()
                                            index = parent.index(child)
                                            parent.insert(index + 1, wrapper)

                                            break

            else:
                # 块级元素直接设置属性
                original_parent.set('_item_id', current_id)
                for child in original_parent.iterdescendants():
                    if child.get("cc-select") is not None:
                        original_parent.set("cc-select", child.get("cc-select"))
                        break

            item_id += 1

            # 保存处理结果
            cleaned_html = etree.tostring(root, method='html', encoding='unicode').strip()
            result.append({
                'html': cleaned_html,
                '_item_id': current_id,
                'content_type': content_type
            })

        except Exception:
            # import traceback
            # print(f'处理段落出错: {traceback.format_exc()}')
            continue

    # 组装最终HTML
    simplified_html = '<html><head><meta charset="utf-8"></head><body>' + ''.join(
        p['html'] for p in result) + '</body></html>'

    return post_process_html(simplified_html)


def simplify_html(html_str) -> etree.Element:
    """
   :return:
       simplified_html: 精简HTML
       original_html: 添加_item_id的原始HTML
       _xpath_mapping: xpath映射
   """
    # 使用selectolax的HTMLParser来修复html
    try:
        soup = HTMLParser(html_str)
        fixed_html = soup.html
    except Exception:
        soup = BeautifulSoup(html_str, 'html.parser')
        fixed_html = str(soup)

    preprocessed_html = remove_xml_declaration(fixed_html)
    # 注释通过lxml的HTMLParser的remove_comments参数处理
    parser = html.HTMLParser(remove_comments=True)
    original_dom = html.fromstring(preprocessed_html, parser=parser)
    # 添加data_uid
    add_data_uids(original_dom)
    original_uid_map = build_uid_map(original_dom)

    # 创建处理用的DOM（深拷贝）
    processing_dom = copy.deepcopy(original_dom)
    # 清理DOM
    remove_tags(processing_dom)
    remove_specific_elements(processing_dom)

    # 提取段落（会记录原始元素引用）
    paragraphs = extract_paragraphs(processing_dom, original_uid_map, include_parents=False)

    # 处理段落（同步添加ID）
    simplified_html = process_paragraphs(paragraphs, original_uid_map)

    remove_all_uids(original_dom)
    original_html = etree.tostring(original_dom, pretty_print=True, method='html', encoding='unicode')

    return simplified_html, original_html
