"""
测试extractor_chain.py， 集成测试：
测试方法是：
1. 设定一个场景：从一些散落的html中提取content_list
2. 定义extractor_pipe的config配置文件，定义chain的执行顺序和模块，数据路径
3. 准备一些html文件，按照零散html的输入标准组织成jsonl数据
4. 执行解析，得到content_list，并比对期望结果

测试需要涵盖：
1. 正确提取时候的content_list是否符合期望
2. 各类异常的抛出是否符合期望
"""
import json
import os
import unittest

from lxml import html

from llm_web_kit.config.cfg_reader import load_pipe_tpl
from llm_web_kit.extractor.extractor_chain import ExtractSimpleFactory
from llm_web_kit.extractor.html.recognizer.cc_math.common import (CSDN, ZHIHU,
                                                                  MathType)
from llm_web_kit.input.datajson import DataJson
from llm_web_kit.libs.doc_element_type import DocElementType, ParagraphTextType


def normalize_html(html_string:str) -> str:
    # 解析 HTML
    tree = html.fromstring(html_string)
    # 转换为字符串并去除空白
    return html.tostring(tree, pretty_print=True, encoding='utf-8').strip()


class TestExtractorChain(unittest.TestCase):
    """Test extractor suit with HTML data."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.html_data_path = os.path.join(self.base_path, 'assets/extractor_chain_input/good_data/html_data_input.jsonl')
        self.md_output_file_path = os.path.join(self.base_path, 'assets/extractor_chain_input/good_data/output_expected/1.md')
        self.txt_output_file_path = os.path.join(self.base_path, 'assets/extractor_chain_input/good_data/output_expected/1.txt')
        self.main_html_output_file_path = os.path.join(
            self.base_path, 'assets/extractor_chain_input/good_data/output_expected/1.main_html.html'
        )
        self.csdn_lineno_output_file_path = os.path.join(
            self.base_path, 'assets/extractor_chain_input/good_data/output_expected/csdn_lineno.md'
        )
        self.oracle_doc_main_html_path = os.path.join(
            self.base_path, 'assets/extractor_chain_input/good_data/output_expected/oracle_doc.main_html.html'
        )

        self.md_expected_content = open(self.md_output_file_path, 'r', encoding='utf-8').read()
        self.txt_expected_content = open(self.txt_output_file_path, 'r', encoding='utf-8').read()
        self.main_html_expected_content = open(self.main_html_output_file_path, 'r', encoding='utf-8').read()
        self.csdn_lineno_expected_content = open(self.csdn_lineno_output_file_path, 'r', encoding='utf-8').read()
        self.oracle_doc_main_html_content = open(self.oracle_doc_main_html_path, 'r', encoding='utf-8').read()

        self.data_json = []
        with open(self.html_data_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                self.data_json.append(json.loads(line))

        assert len(self.data_json) == 104

        # Config for HTML extraction
        self.config = load_pipe_tpl('html-test')

    def test_html_pipeline(self):
        """Test HTML extractor with sample data."""
        # Initialize extractor
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[0]
        # Create DataJson from test data
        input_data = DataJson(test_data)

        # Test extraction
        result = chain.extract(input_data)

        # Verify basic properties
        self.assertEqual(result.get_dataset_name(), 'test_pipeline_suit')
        self.assertEqual(result.get_file_format(), 'HTML')
        self.assertEqual(result['track_id'], 'f7b3b1b4-0b1b')

        html_content_list = result.get_content_list()[0]
        # Verify content_list
        self.assertEqual(result.get_content_list().length(), 1)
        html_content = html_content_list[0]
        # 首先是h1
        self.assertEqual(html_content['type'], DocElementType.TITLE)
        self.assertEqual(html_content['content']['level'], '1')
        self.assertEqual(html_content['content']['title_content'], 'Heading 1')
        # 然后是p
        html_content = html_content_list[1]
        self.assertEqual(html_content['type'], DocElementType.PARAGRAPH)
        self.assertEqual(html_content['content'][0]['c'], 'Paragraph 1')
        self.assertEqual(html_content['content'][0]['t'], ParagraphTextType.TEXT)
        # 然后是img
        html_content = html_content_list[2]
        self.assertEqual(html_content['type'], DocElementType.IMAGE)
        self.assertEqual(html_content['content']['title'], 'image-title')
        self.assertEqual(html_content['content']['alt'], 'image-alt')
        self.assertEqual(html_content['content']['url'], 'https://www.test.com/test.png')
        self.assertEqual(html_content['content']['caption'], '')

        # 然后是simple table
        html_content = html_content_list[4]
        self.assertEqual(html_content['type'], DocElementType.SIMPLE_TABLE)
        self.assertEqual(html_content['content']['is_complex'], False)
        assert html_content['content']['html'].startswith('<table')

        # 然后是complex table
        html_content = html_content_list[5]
        self.assertEqual(html_content['type'], DocElementType.COMPLEX_TABLE)
        self.assertEqual(html_content['content']['is_complex'], True)

        # 然后是list
        html_content = html_content_list[6]
        self.assertEqual(html_content['type'], DocElementType.LIST)
        self.assertEqual(len(html_content['content']['items']), 2)
        self.assertEqual(html_content['content']['list_attribute'], 'unordered')
        self.assertEqual(html_content['content']['items'][0]['c'], '1')
        self.assertEqual(html_content['content']['items'][1]['c'], '2')

        # 嵌套list
        html_content = html_content_list[7]
        self.assertEqual(html_content['type'], DocElementType.LIST)
        self.assertEqual(len(html_content['content']['items']), 2)
        self.assertEqual(len(html_content['content']['items'][0]['child_list']), 2)
        self.assertEqual(html_content['content']['items'][0]['child_list']['items'][0]['c'], '1.1')
        self.assertEqual(html_content['content']['items'][1]['child_list']['items'][0]['c'], '2.1')

        # 行间公式
        html_content = html_content_list[8]
        self.assertEqual(html_content['type'], DocElementType.EQUATION_INTERLINE)
        self.assertEqual(html_content['content']['math_content'], 'x=\\frac{-b±\\sqrt{{b}^{2}-4ac}}{2a}\\text{.}')
        self.assertEqual(html_content['content']['math_type'], MathType.MATHML)

        # 代码
        html_content = html_content_list[9]
        self.assertEqual(html_content['type'], DocElementType.CODE)
        self.assertEqual(len(html_content['content']['code_content']), 251)
        self.assertEqual(html_content['content']['by'], 'tag_pre_code')
        self.assertEqual(html_content['inline'], False)

        # 有序列表
        html_content = html_content_list[10]
        self.assertEqual(html_content['type'], DocElementType.LIST)
        self.assertEqual(html_content['content']['list_attribute'], 'ordered')
        self.assertEqual(len(html_content['content']['items']), 2)
        self.assertEqual(html_content['content']['items'][0]['c'], '100')
        self.assertEqual(html_content['content']['items'][1]['c'], '200')

        # code 前的文本
        html_content = html_content_list[11]
        self.assertEqual(html_content['type'], DocElementType.PARAGRAPH)
        self.assertEqual(len(html_content['content']), 2)
        self.assertEqual(html_content['content'][0]['c'], 'reference:')
        self.assertEqual(html_content['content'][0]['t'], ParagraphTextType.TEXT)
        self.assertEqual(html_content['content'][1]['c'], '#include<xxxx.hpp>')
        self.assertEqual(html_content['content'][1]['t'], ParagraphTextType.CODE_INLINE)

        # txt格式
        txt_content = result.get_content_list().to_txt()
        self.assertEqual(txt_content, self.txt_expected_content)
        self.assertNotEqual(txt_content[-2], '\n')
        self.assertEqual(txt_content[-1], '\n')

        # md格式
        md_content = result.get_content_list().to_nlp_md()
        self.assertEqual(md_content, self.md_expected_content)
        self.assertNotEqual(md_content[-2], '\n')
        self.assertEqual(md_content[-1], '\n')

        # main_html
        main_html = result.get_content_list().to_main_html()  # 获取main_html内容
        self.assertEqual(main_html, self.main_html_expected_content)  # 如果遇到嵌套的html, 则返回原始html的时候还是应当拼接替换一下 TODO

    def test_html_pipeline_suit_2(self):
        """测试第二个数据：这个数据会丢失一些文本信息."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[1]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        # Verify basic properties
        self.assertEqual(result.get_dataset_name(), 'test_pipeline_suit')
        self.assertEqual(result['track_id'], 'stackoverflow_math')

        html_content_list = result.get_content_list()[0]
        assert len(html_content_list) == 22

    def test_mathlab_html_to_md(self):
        """测试第二个数据：这个数据会丢失一些文本信息."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[2]  # matlab网页
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)

        # Verify basic properties
        self.assertEqual(result['track_id'], 'mathlab_code')
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn('### Use Integers for Index Variables', md_content)
        self.assertIn('### Limit Use of `assert` Statements', md_content)

    def test_list_to_md(self):
        """测试第三个数据：这个数据会丢失一些文本信息."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[3]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        self.assertEqual(result['track_id'], 'educba_com_list')
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn('- Exception: All exceptions base class', md_content)

    def test_code_mix_in_list(self):
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[4]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn('The descendant of `StandardizerActionRunner` interface has to provide', md_content)

    def test_code_pre_mixed(self):
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)

        test_data = self.data_json[5]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        # print("code_pre_mixed", result.get_content_list().to_mm_md())
        self.assertIn("""```
this (DEFAULT_SERVER_NAME, DEFAULT_SERVER_PORT);
```

Test Test Test

```
ABC
DEF
```""", result.get_content_list().to_mm_md())

    def test_image_without_path(self):
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)

        test_data = self.data_json[6]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        self.assertIn('![點(diǎn)擊進(jìn)入下一頁(yè)](dda09be3795fa0df88c094ca906adf77086f1741b4d5634536997146deeda777)', result.get_content_list().to_mm_md())
        self.assertNotIn('![點(diǎn)擊進(jìn)入下一頁(yè)](dda09be3795fa0df88c094ca906adf77086f1741b4d5634536997146deeda777)', result.get_content_list().to_txt())

    def test_lineno_detect(self):
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[7]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        code_content = result.get_content_list()[0][0]['content']['code_content']
        self.assertEqual(code_content, self.csdn_lineno_expected_content)

    def test_lineno_detect_2(self):
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[8]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        self.assertIn('12.1.  Normative References', result.get_content_list().to_mm_md())

    def test_legato_docs_code_with_comment(self):
        """
        magic-html 抽代码时候把注释抽没了
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[9]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        assert result is not None
        # TODO magic-html修改完毕后，再来完善断言

    def test_oracle_doc_comment(self):
        """
        把末尾部分抽没了
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[10]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        main_html = result.get_content_list().to_mm_md()
        assert 'public int hashCode()' in main_html

    def test_table_involve_inline_code(self):
        """
        table里面包含行内code
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[11]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_list = result.get_content_list()._get_data()[0][0]['content']['html']
        assert content_list == '<table><tr><th>Function</th><th>Description</th><th>Example</th></tr><tr><td><cccode-inline>`print()`</cccode-inline></td><td>Prints a message to the console.</td><td><cccode-inline>`print("Hello, World!")`</cccode-inline></td></tr><tr><td><cccode-inline>`len()`</cccode-inline></td><td>Returns the length of an object.</td><td><cccode-inline>`len([1, 2, 3])`</cccode-inline></td></tr><tr><td><cccode-inline>`range()`</cccode-inline></td><td>Generates a sequence of numbers.</td><td><cccode-inline>`range(1, 10)`</cccode-inline></td></tr></table>'

    def test_table_tail_text(self):
        """table的tail文本保留."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[12]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '| ID: 975' in content_md

    def test_table_element_include_enter(self):
        """table的元素中间有换行."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[13]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '''| عنوان فارسی | توسعه مالی و هزینه سرمایه حقوق سهامداران: شواهدی از چین |
|---|---|
| عنوان انگلیسی | Financial development and the cost of equity capital: Evidence from China |
| کلمات کلیدی : | &nbsp توسعه مالی؛ هزینه سرمایه حقوق سهامداران؛ قانون و امور مالی؛ چین |
| درسهای مرتبط | حسابداری |''' in content_md

    def test_list_empty(self):
        """list抽取为空，原因是嵌套的img标签没有text."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[14]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        list_type = result.get_content_list()._get_data()[0][0]['type']
        assert list_type != 'list'

    def test_table_include_math_p(self):
        """table包含math和其他内容."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[15]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_list = result.get_content_list()._get_data()
        assert len(content_list[0]) == 17
        assert content_list[0][3]['content']['html'] == "<table><tr><td>up vote 17 down vote favorite\n\n5</td><td>I'm having problems with exercises on proving whether or not a given number is prime. Is $83^{27} + 1$ prime?\n\nprime-numbers factoring<table><tr><td></td><td></td><td></td></tr></table></td></tr><tr><td></td><td></td></tr></table>"

    def test_table_include_math_p_2(self):
        """table包含math和其他内容."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[16]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        # with open('output_badcase_p2.md', 'w', encoding='utf-8') as f:
        #     f.write(md_content)
        self.assertIn('<table><tr><td>单位换算：</td><td>数学公式区块： $1\\text{km}={10}^{3}\\text{m}$<table><tr><td>长度</td><td>质量</td><td>时间</td></tr>', md_content)

    def test_clean_tags(self):
        """测试clean_tag的preExtractor是否生效."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[17]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        self.assertNotIn('begingroup', content_md)

    def test_list_nest_three(self):
        """测试列表嵌套三层."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[18]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_content_list = result.get_content_list()._get_data()
        print('============= result_content_list', json.dumps(result_content_list, ensure_ascii=False))
        assert int(result_content_list[0][0]['content']['list_nest_level']) == 3

    def test_table_include_entity(self):
        """测试table包含实体."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[19]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_mm_md()
        assert '&amp;' not in result_md
        assert '&nbsp;' not in result_md

    def test_content_list_empty(self):
        """测试content_list为空."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[20]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_mmd = result.get_content_list().to_mm_md()
        assert '京大平层，奶油风浪漫到家！' in content_mmd

    def test_nlp_md_exclude_node_types(self):
        """测试nlp_md排除节点类型."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[21]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_txt = result.get_content_list().to_nlp_md(exclude_nodes=[DocElementType.COMPLEX_TABLE])
        assert '<table>' not in content_txt
        assert '</table>' not in content_txt

    def test_para_is_short(self):
        """测试para识别后内容太短."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[22]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_txt = result.get_content_list().to_nlp_md()
        assert len(content_txt) == 1983

    def test_xml_tag(self):
        """测试xml标签."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[23]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_mm_md()
        self.assertIn('Every child that attends a CHICKS break has a deserving story', result_md)

    @unittest.skip("暂时不检查美元转义")
    def test_math_dollar(self):
        """测试math美元符号."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[24]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        self.assertIn(r'\$16.8 million', result_md)

    def test_math_non_asciimath(self):
        """测试普通文本中的``不应该被识别为asciimath."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[25]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        self.assertIn(r'\`Queen Helena\`', result_md)

    def test_more_nt(self):
        """测试去除单元格的\n\t.\n保留下来."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[26]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_content_list = result.get_content_list()._get_data()
        result = result_content_list[0][2]['content']['html']
        assert '\n\t' not in result
        assert len(result) == 1893

    def test_math_physicsforums(self):
        """测试math_physicsforums网页中数学公式是[tex]和[itex]包裹的，且中间还有<br>标签分割."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[27]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        self.assertIn('$\\Delta K = (dd^{\\dagger} + d^{\\dagger}d)K$', result_md)
        self.assertIn('$$\\Delta K = \\Bigl( \\frac{1}{3!}\\epsilon^{klm}\\epsilon^n_{\\ ij}\\partial_k \\partial_n K_{lm} - \\frac{1}{4}\\partial_{i}\\partial^k K_{jk} \\Bigr) dx^i \\wedge dx^j$$', result_md)

    @unittest.skip("暂时不检查美元转义")
    def test_table_only_include_tr(self):
        """测试table的表头只包含tr标签."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[28]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        assert r'List Price: \$11.80' in result_md

    def test_table_only_one_td(self):
        """测试table只有一个td."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[29]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        assert '|  | Shooting on DEWEY AVENUE AND GLENDALE PARK., ROCHESTER |\n|---|---|' not in result_md

    def test_math_broken_label(self):
        """测试math标签包含属性缺失的情况."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[30]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        self.assertIn(r'$alpha = \left(alpha_1, alpha_2, ldots, alpha_n\right) ,!$', result_md)

    def test_table_span_error(self):
        """测试table的span标签错误."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[31]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_flag = result.get_content_list()._get_data()[0][0]['content']['is_complex']
        assert result_flag is True

    def test_table_colspan_error(self):
        """测试table的colspan标签为字符串引起的异常错误."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[32]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_flag = result.get_content_list()._get_data()[0][15]['content']['is_complex']
        assert result_flag is False

    def test_table_colspan_percent_err(self):
        """测试table的colspan标签为百分数引起的异常错误."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[33]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_flag = result.get_content_list()._get_data()[0][0]['content']['is_complex']
        assert result_flag is True

    def test_table_colspan_str_error(self):
        """测试table的colspan标签为字符串引起的异常错误."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[34]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_flag = result.get_content_list()._get_data()[0][28]['content']['is_complex']
        assert result_flag is False

    def test_table_invalid_percent(self):
        """测试table的colspan标签为百分数引起的异常错误."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[35]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_flag = result.get_content_list()._get_data()[0][0]['content']['is_complex']
        assert result_flag is False

    def test_maigc_html(self):
        """测试magic-html."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[36]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_magic_html()
        assert len(result_md) > 0

    def test_table_tail_repeat(self):
        """测试table的tail重复."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[37]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_mm_md()
        text = """
A few explanations on why certain things in business are so.
        """
        assert result_md.count(text.strip()) == 1

    def test_title_include_special_char(self):
        """测试title包含特殊字符."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[38]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list()._get_data()
        assert result_md[0][0]['content']['title_content'] == 'View source for Semi-continuous decomposition'

    def test_list_lack_content(self):
        """list缺少a标签前内容.html格式不标准."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[39]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_nlp_md()
        assert '猜你感兴趣' in result_md
        assert '友情链接' in result_md

    def test_table_lack_pre_content(self):
        """测试table缺少td标签前面的内容."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[40]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_content_list = result.get_content_list()._get_data()
        assert result_content_list[0][22]['content']['html'] == '<table><tr><th>お名前【必須】</th><td></td><th>お名前（カナ）</th><td></td></tr><tr><th>ご連絡先【いずれか必須】</th><td colspan="3"><table><td>メールアドレス</td><td>電話番号</td></table>※メール受信制限をしている方は、@chintai.co.jpからのメールを受信できるよう設定の変更をお願い致します。</td></tr></table>'

    def test_td_include_specila_symbol(self):
        """测试td包含特殊符号|，需要转义."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[42]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        result_md = result.get_content_list().to_mm_md()
        assert result_md == r"""| \| 你好 | 字 | 字 |
|---|---|---|
| \| 字 | 字 | 字 |
| 字 | 字 | 字 |
"""

    def test_nest_list(self):
        """测试嵌套列表."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[43]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        assert """- Thread
  - amperehours apere-hours convert coulombs coulumbs electricty joules kilowatthours
  - Replies: 4
  - Forum: Classical & Modern Physics""" in content_md

    def test_definition_list(self):
        """测试定义列表."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[44]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        assert '2. 苍南县龙港林冉小吃店' not in content_md

    def test_cc_label_exception(self):
        """测试cc_label_exception."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[45]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        assert len(content_md) > 0

    def test_not_html(self):
        """测试not_html."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[46]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        main_html = result.get_magic_html()
        print(main_html)
        content_md = result.get_content_list()._get_data()
        print(json.dumps(content_md, ensure_ascii=False))

    def test_timeout_exception(self):
        import time
        """测试timeout异常."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        for index in range(48, 49):
            test_data = self.data_json[index]
            # 开始计时
            start_time = time.time()
            input_data = DataJson(test_data)
            result = chain.extract(input_data)
            content_md = result.get_content_list().to_mm_md()
            end_time = time.time()    # 结束计时
            elapsed_time = end_time - start_time
            with open('output.md', 'w', encoding='utf-8') as f:
                f.write(content_md)
            assert elapsed_time < 30
            assert len(content_md) > 0

    def test_math_namespace(self):
        """badcase1，math标签缺少命名空间."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[87]
        # 创建 DataJson 并提取内容
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        # with open('output_badcase1-1.md', 'w', encoding='utf-8') as f:
        #     f.write(md_content)
        # 分别测试一个行内公式和一个行间公式
        self.assertIn(
            r'$\left(1+{\text{DP}}_{0}/\left({\sum }_{\text{n}=0}^{\text{i}}\left({\text{DP}}_{\text{n}}\right)×\text{C}\right)\right)$',
            md_content)
        self.assertIn(r'\left(1+\frac{D{P}_{0}}{{\sum }_{n=0}^{i}\left(D{P}_{n}\right)×C}\right)×D{P}_{i+1}=\frac{\left\{{\sum }_{n=0}^{i}\left(D{O}_{n}\right)+P\right\}×D{P}_{0}}{\left\{{\sum }_{n=0}^{i}\left(D{P}_{n}\right)×C\right\}}\left(D{O}_{0}=0,i\ge 0\right)', md_content)

    def test_math_paragraph(self):
        """badcase2，段落划分错误导致公式不在同段落."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[88]
        # Create DataJson from test data
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        # 打印content_list内容
        # content_list = result.get_content_list()._get_data()
        # print('Content List:', json.dumps(content_list, ensure_ascii=False, indent=2))
        self.assertIn(r'1178.7 F g ${}^{-1}$', md_content)

    def test_csnd_none_formula(self):
        """badcase3，新增csdn公式提取逻辑."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[89]
        # 验证URL中包含blog.csdn.net
        self.assertIn(CSDN.DOMAIN, test_data['url'])
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn(r'$\lim\limits_{x \to 1}\dfrac{x^2-1}{x-1}$', md_content)
        self.assertIn(r'\begin{aligned} \frac{f(1.01)-f(1)}{1.01-1} &= \frac{1.01^2-1^2}{0.01} \\ &= \frac{0.0201}{0.01} \\ &= 2.01\end{aligned}', md_content)

    def test_zhihu_custom_tag(self):
        """测试知乎自定义标签."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[97]
        # 验证URL中包含zhuanlan.zhihu.com
        self.assertIn(ZHIHU.DOMAIN, test_data['url'])
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn(r'\begin{gathered} p(s_{1}|s_{1},a_{2})=0, \\ p(s_{2}|s_{1},a_{2})=1, \\ p(s_{3}|s_{1},a_{2})=0, \\ p(s_{4}|s_{1},a_{2})=0, \\ p(s_{5}|s_{1},a_{2})=0, \end{gathered}', md_content)
        self.assertIn(r'$s_1\xrightarrow{a_2}s_2\xrightarrow{a_3}s_5\xrightarrow{a_3}s_8\xrightarrow{a_2}s_9.$', md_content)
        self.assertIn(r'$\mathrm{return}=0+0+0+1=1.$', md_content)
        self.assertIn(r'\begin{aligned} V(s) & =\mathbb{E}[G_t|S_t=s] \\  & =\mathbb{E}[R_t+\gamma R_{t+1}+\gamma^2R_{t+2}+\ldots|S_t=s] \\  & =\mathbb{E}[R_t+\gamma(R_{t+1}+\gamma R_{t+2}+\ldots)|S_t=s] \\  & =\mathbb{E}[R_t+\gamma G_{t+1}|S_t=s] \\  & =\mathbb{E}[R_t+\gamma V(S_{t+1})|S_t=s] \end{aligned}', md_content)

    def test_mathinsight_custom_latex(self):
        """测试mathinsight自定义latex."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[98]
        # 验证URL中包含mathinsight.org
        # self.assertIn('mathinsight.org', test_data['url'])
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn(r'L(\mathbf{x}) = f(\mathbf{a}) + T(\mathbf{x}-\mathbf{a})', md_content)
        self.assertIn(r'\frac{x^2y}{x^2+y^2} & \text{if } (x,y) \ne (0,0)\\',md_content)

    def test_mjx_container(self):
        """测试mathinsight自定义latex."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[99]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn(r'1111', md_content)
        # content_list = result.get_content_list()._get_data()
        # print('Content List:', json.dumps(content_list, ensure_ascii=False, indent=2))
        # with open('test_mjx_container.md', 'w', encoding='utf-8') as f:
        #     f.write(md_content)

    def test_ascii_delimiter(self):
        """测试ascii分隔符."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[101]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn(r'$f = \frac{1}{T} ^ 2 \sqrt{\frac{A E}{\rho}}$', md_content)
        self.assertIn(r'${m}^{2}$', md_content)
        self.assertIn(r'\rho$', md_content)
        self.assertIn(r'$f = \frac{1}{2 L} \sqrt{\frac{E}{\rho}}$', md_content)
        self.assertIn(r'$L = {T}^{2} / \left(2 W\right)$', md_content)

    def test_mathjax_mock(self):
        """测试虚拟mathjax渲染器."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[103]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        self.assertIn(r'$(a_n)$', md_content)
        self.assertIn(r'$a_n ≤ a_{n+1}$', md_content)
        self.assertIn(r'$n \in \mathbb{N}$', md_content)
        self.assertIn(r'$\left ( \frac{1}{n} \right ) = (1, \frac{1}{2}, \frac{1}{3}, ..., \frac{1}{n}, \frac{1}{n+1}, ... )$', md_content)

    def test_htmlmath_sub_sup(self):
        """测试htmlmath中的上下标标签."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[102]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        md_content = result.get_content_list().to_nlp_md()
        # with open('test0725_sub.md', 'w', encoding='utf-8') as f:
        #     f.write(md_content)
        self.assertIn(r'<sub>4</sub>', md_content)
        self.assertIn(r'<sub>8</sub>', md_content)
        self.assertIn(r'<sub>2</sub>', md_content)
        self.assertIn(r'<sub>g</sub>', md_content)
        self.assertIn(r'<sub>u</sub>', md_content)

    def test_double_ul(self):
        """测试双重ul标签."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[90]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        assert 'Wheels and Tyres' in content_md

    def test_other_space(self):
        """测试括号、双引单引号等中文符号导致的空格."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[91]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        assert '(APC)' in content_md
        test_data = self.data_json[92]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        assert '“I do swear by the Day of Resurrection.' in content_md

    def test_classname_to_code(self):
        """测试由于classname导致的audio、list识别为code的情况."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[93]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_list = result.get_content_list().to_dict()[0]
        types = []
        # 1
        for i in range(len(content_list)):
            types.append(content_list[i]['type'])
        with open('output.jsonl', 'w') as f:
            f.write(result.get_content_list().to_json())
        assert 'code' not in types
        test_data = self.data_json[94]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_list = result.get_content_list().to_dict()[0]
        types = []

        for i in range(len(content_list)):
            types.append(content_list[i]['type'])
        assert 'code' not in types

    def test_sup_escape_error(self):
        """测试<sup>和<sub>被转义成<sup&gt;和<sub&gt;导致上下标失效的情况."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[95]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_nlp_md()
        # print(content_md)
        assert '<sup&gt;' not in content_md and '<sub&gt;' not in content_md

    def test_item_notext_error(self):
        """测试跳过list item中无实际内容的情况."""
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = self.data_json[96]
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_list = result.get_content_list().to_dict()[0]
        first_item_list = {}
        for i in range(len(content_list)):
            if content_list[i]['type'] == 'list':
                first_item_list = content_list[i]['content']['items']
                break
        assert len(first_item_list) == 0
