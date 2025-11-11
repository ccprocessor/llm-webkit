import re
import unittest
from pathlib import Path

from lxml import html

from llm_web_kit.input.pre_data_json import PreDataJson, PreDataJsonKey
from llm_web_kit.main_html_parser.parser.tag_simplifier import \
    HtmlTagSimplifierParser

base_dir = Path(__file__).resolve().parent


class MyTestCase(unittest.TestCase):
    def check_and_find_max_item_id(self, input_str: str) -> int:
        # 匹配所有 _item_id="XXX" 的模式，提取XXX部分
        pattern = "_item_id" + r'="(\d+)"'
        matches = re.findall(pattern, input_str)

        # 至少匹配一个
        if len(matches) == 0:
            return 0

        # 匹配到的对象全部转化为int
        int_list = []
        for match in matches:
            try:
                int_list.append(int(match))
            except Exception:
                raise ValueError(f'error while convert match {match} to int')

        # 检查是否为从1开始的连续整数
        target_value = 1
        for int_id in int_list:
            if int_id == target_value:
                target_value += 1
            else:
                raise ValueError(
                    f'mistake find in int list, current target value is {target_value}, but find {int_id}' + '\n' + input_str
                )

        # 都没有问题的情况下，返回最大的数
        return int_list[-1]

    def test_tag_simplifier(self):
        file_path = base_dir / 'assets/test_html_data/test_tah_simplifier.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 34)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

    def test_tag_simplifier1(self):
        file_path = base_dir / 'assets/test_html_data/normal_dl.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 48)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

    def test_tag_simplifier2(self):
        file_path = base_dir / 'assets/test_html_data/normal_table.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 11)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

    def test_tag_simplifier3(self):
        file_path = base_dir / 'assets/test_html_data/special_table_1.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 41)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

    def test_tag_simplifier4(self):
        file_path = base_dir / 'assets/test_html_data/1.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html, PreDataJsonKey.IS_XPATH: False}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 113)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

    def test_tag_simplifier_table(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/table.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 35)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位data-anno-uid="anno-uid-3vtzg9uxee4"的table元素，该table用于布局
        table_element = id_dom.xpath('//table[@data-anno-uid="anno-uid-3vtzg9uxee4"]')[0]
        # 确认该table元素没有_item_id属性
        self.assertEqual(table_element.get('_item_id'), None)
        # 确认该table的3个td元素的内部都包含若干个存在_item_id属性的元素
        for td_element in table_element.xpath('./tbody/tr/td'):
            td_item_count = 0
            for child in td_element.iter():
                if child.get('_item_id') is not None:
                    td_item_count += 1
            self.assertNotEqual(td_item_count, 0)

    def test_tag_simplifier_data_table(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/data_table.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 105)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位带有data-table属性的table元素
        table_element = id_dom.xpath('//table[@data-table]')[0]
        # 确认该table元素有_item_id属性
        self.assertIsNotNone(table_element.get('_item_id'))

    def test_tag_simplifier_nested_table_colgroup(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/nested_table_colgroup.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 13)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位外层table元素，该table用于布局
        table_element = id_dom.xpath('//table[@class="centralPane"]')[0]
        # 确认该table元素没有_item_id属性
        self.assertIsNone(table_element.get('_item_id'))

        # 用xpath定位内层table元素，该table是数据表格，<table>标签内存在colgroup元素
        table_element = id_dom.xpath('//table[@class="miscTable"]')[0]
        # 确认该table元素有_item_id属性
        self.assertIsNotNone(table_element.get('_item_id'))

    def test_tag_simplifier_nested_table_headers(self):
        # 测试表格的单元格中包含headers属性的情况，这个测试用例中的表格单元格存在headers属性，但是<table>标签内不包含colgroup元素
        file_path = base_dir / 'assets/test_html_data/simplify_cases/nested_table_headers.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 13)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位外层table元素，该table用于布局
        table_element = id_dom.xpath('//table[@class="centralPane"]')[0]
        # 确认该table元素没有_item_id属性
        self.assertIsNone(table_element.get('_item_id'))

        # 用xpath定位内层table元素，该table是数据表格，其单元格包含headers属性
        table_element = id_dom.xpath('//table[@class="miscTable"]')[0]
        # 确认该table元素有_item_id属性
        self.assertIsNotNone(table_element.get('_item_id'))

    def test_tag_simplifier_nested_table_caption(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/nested_table_caption.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 14)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位外层table元素，该table用于布局
        table_element = id_dom.xpath('//table[@data-anno-uid="anno-uid-xgzpvn8fnqk"]')[0]
        # 确认该table元素没有_item_id属性
        self.assertIsNone(table_element.get('_item_id'))

        # 用xpath定位内层table元素，该table是数据表格，其包含caption元素
        table_element = id_dom.xpath('//table[@data-anno-uid="anno-uid-olo3onur84"]')[0]
        # 确认该table元素有_item_id属性
        self.assertIsNotNone(table_element.get('_item_id'))

    def test_tag_simplifier_list(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/list.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 118)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位ul元素，该ul用于布局
        list_element = id_dom.xpath('//ul[@data-anno-uid="anno-uid-7s58m3hrcz5"]')[0]
        # 确认该ul元素没有_item_id属性
        self.assertIsNone(list_element.get('_item_id'))
        # 确认该ul元素下的li元素内均包含有_item_id属性的元素
        for li_element in list_element.xpath('./li'):
            li_item_count = 0
            for child in li_element.iter():
                if child.get('_item_id') is not None:
                    li_item_count += 1
            self.assertNotEqual(li_item_count, 0)

    def test_tag_simplifier_non_list_child(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/non_list_child.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 151)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位ul元素，该ul用于布局
        list_element = id_dom.xpath('//ul[@data-anno-uid="anno-uid-myobddy8ord"]')[0]
        # 确认该ul元素没有_item_id属性
        self.assertIsNone(list_element.get('_item_id'))
        # 用xpath定位上述ul内部的一个li，该li内部结构复杂，应该包含多个_item_id
        li_element = id_dom.xpath('//li[@data-anno-uid="anno-uid-7wux77fqc7t"]')[0]
        li_item_count = 0
        for child in li_element.iter():
            if child.get('_item_id') is not None:
                li_item_count += 1
        self.assertNotEqual(li_item_count, 0)

    def test_tag_simplifier_inline_block(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/inline_block.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 12)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位span元素，该span内部包含了块级元素
        span_element = id_dom.xpath('//span[@data-anno-uid="anno-uid-yrlyp4ay0l"]')[0]
        # 确认该span元素没有_item_id属性
        self.assertIsNone(span_element.get('_item_id'))
        # 该span元素内部包含多个块级元素，每个块级元素都包含_item_id属性
        for child in span_element.iterchildren():
            self.assertIsNotNone(child.get("_item_id"))

    def test_tag_simplifier_abnormal_comment(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/abnormal_comment.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 53)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        # 验证不规范的注释内包含的有效内容没有被删除
        self.assertIn('<body class="thrColLiqHdr">', raw_tag_html)
        # 验证规范的注释都已被删除
        comment_res = re.search(r'<!--.*?-->', raw_tag_html, flags=re.DOTALL)
        self.assertIsNone(comment_res)

    def test_tag_simplifier_header_tag(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/header_tag.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 35)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位元素，该元素位于id名为header的元素内部，且这个'header'是body的直接子元素
        header_element = id_dom.xpath('//h1[@data-anno-uid="anno-uid-g513k4pfha8"]')[0]
        # 确认该元素有_item_id属性，也就是被保留了
        self.assertIsNotNone(header_element.get('_item_id'))
        # 用xpath定位元素，该元素位于header标签内部，但这个header不是body的直接子元素
        header_element = id_dom.xpath('//h2[@data-anno-uid="anno-uid-g8cyd0j0kn6"]')[0]
        # 确认该元素有_item_id属性，也被保留了（目前的simplify是所有的header都保留）
        self.assertIsNotNone(header_element.get('_item_id'))

    def test_tag_simplifier_nav_class(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/nav_class.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 58)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位元素，该元素的class是nav，但不是body的直接子元素，应该保留
        nav_element = id_dom.xpath('//div[@data-anno-uid="anno-uid-v6mugwj7iv"]')[0]
        # 验证nav内部有_item_id属性的元素，证明nav没有被删除
        nav_item_count = 0
        for child in nav_element.iter():
            if child.get('_item_id') is not None:
                nav_item_count += 1
        self.assertNotEqual(nav_item_count, 0)

        nav_element = id_dom.xpath('//div[@data-anno-uid="anno-uid-189mlskr0fc"]')[0]
        self.assertIsNone(nav_element.get("_item_id"))

    def test_tag_simplifier_block_select(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/block_select.html'
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 7)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)

        id_dom = html.fromstring(raw_tag_html)
        # 用xpath定位元素，该元素是块级元素且内部不包含块级元素，但该元素本身没有cc-select，只是其内部元素有cc-select
        p_element = id_dom.xpath('//p[@data-anno-uid="anno-uid-tnbktgx26s"]')[0]
        # 验证该元素被加上了_item_id和cc-select
        self.assertIsNotNone(p_element.get("_item_id"))
        self.assertIsNotNone(p_element.get("cc-select"))

    def test_tag_simplifier_unusual_encoding(self):
        file_path = base_dir / 'assets/test_html_data/simplify_cases/unusual_encoding.html'
        with open(file_path, 'r') as file:
            raw_html = file.read()

        data_dict = {PreDataJsonKey.TYPICAL_RAW_HTML: raw_html}
        pre_data = PreDataJson(data_dict)

        pre_data_result = HtmlTagSimplifierParser({}).parse(pre_data)

        simplifier_raw_html = pre_data_result.get(PreDataJsonKey.TYPICAL_SIMPLIFIED_HTML, '')
        simple_id_count = self.check_and_find_max_item_id(simplifier_raw_html)
        self.assertEqual(simple_id_count, 102)

        raw_tag_html = pre_data_result.get(PreDataJsonKey.TYPICAL_RAW_TAG_HTML, '')
        tag_id_count = self.check_and_find_max_item_id(raw_tag_html)
        self.assertEqual(tag_id_count, simple_id_count)


if __name__ == '__main__':
    unittest.main()
