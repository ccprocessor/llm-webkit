import json
import unittest
from pathlib import Path

from llm_web_kit.extractor.html.recognizer.recognizer import CCTag
from llm_web_kit.extractor.html.recognizer.table import TableRecognizer
from llm_web_kit.libs.html_utils import html_to_element

TEST_CASES = [
    {
        'input': (
            'assets/recognizer/table.html',
            'assets/recognizer/table_exclude.html',
            'assets/recognizer/only_table.html',
            'assets/recognizer/table_simple_compex.html',
            'assets/recognizer/table_to_content_list_simple.html',
            'assets/recognizer/table_to_content_list_complex.html',
            'assets/recognizer/table_include_image.html',
            'assets/recognizer/table_simple_cc.html',
            'assets/recognizer/table_include_rowspan_colspan.html',
            'assets/recognizer/table_involve_equation.html',
            'assets/recognizer/table_include_after_code.html',
            'assets/recognizer/table_involve_code.html',
            'assets/recognizer/table_involve_complex_code.html'

        ),
        'expected': [
            ('assets/recognizer/table_to_content_list_simple_res.json'),
            ('assets/recognizer/table_to_content_list_complex_res.json'),
            ('assets/recognizer/table_include_image_expcet.json'),
            ('assets/recognizer/table_include_code_expect.json')
        ],
    }
]

base_dir = Path(__file__).parent


class TestTableRecognizer(unittest.TestCase):
    def setUp(self):
        self.rec = TableRecognizer()

    def test_involve_cctale(self):
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][0])
            base_url = test_case['input'][1]
            raw_html = raw_html_path.read_text()
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            self.assertEqual(len(parts), 4)

    def test_not_involve_table(self):
        """不包含表格."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][1])
            base_url = test_case['input'][1]
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            self.assertEqual(len(parts), 1)

    def test_only_involve_table(self):
        """只包含表格的Html解析."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][2])
            base_url = test_case['input'][1]
            raw_html = raw_html_path.read_text()
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            self.assertEqual(len(parts), 2)
            table_body = parts[1][0].text_content()
            assert table_body == '<table><tr><td>Mrs S Hindle</td></tr><tr><td>Show</td><td>CC</td><td>RCC</td></tr><tr><td>Driffield 5th October 2006</td><td>CH. Ricksbury Royal Hero</td><td>CH. Keyingham Branwell</td></tr><tr><td>Manchester 16th January 2008</td><td>CH. Lochbuie Geordie</td><td>Merryoth Maeve</td></tr><tr><td>Darlington 20th September 2009</td><td>CH. Maibee Make Believe</td><td>CH. Loranka Just Like Heaven JW</td></tr><tr><td>Blackpool 22nd June 2012</td><td>CH. Loranka Sherrie Baby</td><td>Dear Magic Touch De La Fi Au Songeur</td></tr><tr><td>Welsh Kennel Club 2014</td><td>Brymarden Carolina Sunrise</td><td>Ch. Wandris Evan Elp Us</td></tr><tr><td>Welsh Kennel Club 2014</td><td>Ch. Charnell Clematis of Salegreen</td><td>CH. Byermoor Queens Maid</td></tr></table>'

    def test_table_include_img_label(self):
        """table是否包含img标签."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][6])
            base_url = test_case['input'][1]
            raw_html = raw_html_path.read_text()
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            assert len(parts) == 3
            simple_table_tag = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')[0]
            simple_table_type = simple_table_tag.attrib
            assert simple_table_type['table_type'] == 'simple'

    def test_cc_simple_table(self):
        """cc中简单表格."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][7])
            base_url = test_case['input'][8]
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            assert len(parts) == 3
            content = parts[1][0].text_content()
            assert content == '<table><tbody><tr><td>Рейтинг:</td><td>Рейтинг 5.00 из 5 на основе опроса 3 пользователей</td></tr><tr><td>Тип товара:</td><td>Препараты для омоложения</td></tr><tr><td>Форма:</td><td>Крем</td></tr><tr><td>Объем:</td><td>50 мл</td></tr><tr><td>Рецепт:</td><td>Отпускается без рецепта</td></tr><tr><td>Способ хранения:</td><td>Хранить при температуре 4-20°</td></tr><tr><td>Примечание:</td><td>Беречь от детей</td></tr><tr><td>Оплата:</td><td>Наличными/банковской картой</td></tr><tr><td>Доступность в Северске:</td><td>В наличии</td></tr><tr><td>Доставка:</td><td>2-7 Дней</td></tr><tr><td>Цена:</td><td>84 ₽</td></tr></tbody></table>'

    def test_cc_complex_table(self):
        """cc跨行跨列的表格."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][8])
            base_url = test_case['input'][8]
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            assert len(parts) == 3
            content = parts[1][0].text_content()
            assert content == '<table><caption>ফেব্রুয়ারি ২০২৪</caption><thead><tr><th>সোম</th><th>মঙ্গল</th><th>বুধ</th><th>বৃহ</th><th>শুক্র</th><th>শনি</th><th>রবি</th></tr></thead><tfoot><tr><td colspan="3">« জানুয়ারি</td><td></td><td colspan="3"></td></tr></tfoot><tbody><tr><td colspan="3"></td><td>১</td><td>২</td><td>৩</td><td>৪</td></tr><tr><td>৫</td><td>৬</td><td>৭</td><td>৮</td><td>৯</td><td>১০</td><td>১১</td></tr><tr><td>১২</td><td>১৩</td><td>১৪</td><td>১৫</td><td>১৬</td><td>১৭</td><td>১৮</td></tr><tr><td>১৯</td><td>২০</td><td>২১</td><td>২২</td><td>২৩</td><td>২৪</td><td>২৫</td></tr><tr><td>২৬</td><td>২৭</td><td>২৮</td><td>২৯</td><td colspan="3"></td></tr></tbody></table>'
            table_type = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')[0]
            assert table_type.attrib['table_type'] == 'complex'

    def test_simple_complex_table(self):
        """包含简单和复杂table."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][3])
            base_url = test_case['input'][1]
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            simple_table_tag = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')[0]
            simple_table_type = simple_table_tag.attrib
            assert simple_table_type['table_type'] == 'simple'
            assert simple_table_type == {'table_type': 'simple', 'table_nest_level': '1', 'html': '<table>\n    <tr>\n        <td>1</td>\n        <td>2</td>\n    </tr>\n    <tr>\n        <td>3</td>\n        <td>4</td>\n    </tr>\n</table>'}
            complex_table_tag = parts[2][0].xpath(f'.//{CCTag.CC_TABLE}')[0]
            complex_table_type = complex_table_tag.attrib
            assert complex_table_type['table_type'] == 'complex'
            assert complex_table_type == {'table_type': 'complex', 'table_nest_level': '1', 'html': '<table>\n        <tr>\n            <td rowspan="2">1</td>\n            <td>2</td>\n            <td>3</td>\n        </tr>\n        <tr>\n            <td colspan="2">4</td>\n        </tr>\n        <tr>\n            <td>5</td>\n            <td>6</td>\n            <td>7</td>\n        </tr>\n    </table>'}

    def test_table_to_content_list_node_simple(self):
        """测试table的 to content list node方法."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][4])
            base_url = test_case['input'][1]
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parsed_content = raw_html
            result = self.rec.to_content_list_node(base_url, html_to_element(parsed_content), raw_html)
            expect = base_dir.joinpath(test_case['expected'][0])
            expect_json = expect.read_text(encoding='utf-8')
            assert result['type'] == json.loads(expect_json)['type']
            assert result['content']['is_complex'] == json.loads(expect_json)['content']['is_complex']
            assert result['raw_content'] == json.loads(expect_json)['raw_content']
            self.assertTrue(result['content']['html'].startswith('<table>'))
            self.assertTrue(result['content']['html'].endswith('</table>'))

    def test_table_to_content_list_node_complex(self):
        """测试table的 complex table to content list node方法."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][5])
            expect_path = base_dir.joinpath(test_case['expected'][1])
            raw_html = raw_html_path.read_text(encoding='utf-8')
            result = self.rec.to_content_list_node(expect_path, html_to_element(raw_html), raw_html)
            fr = open(expect_path, 'r', encoding='utf-8')
            expect_result = json.loads(fr.read())
            assert result == expect_result

    def test_table_involve_equation(self):
        """involve equation table,待解决嵌套问题."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][9])
            base_url = 'https://en.m.wikipedia.org/wiki/Variance'
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            complex_table_tag = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')
            assert complex_table_tag[0].text == '<table><tbody><tr><th>Name of the probability distribution</th><th>Probability distribution function</th><th>Mean</th><th>Variance</th></tr><tr><td>Binomial distribution</td><td>${\\displaystyle \\Pr \\,(X=k)={\\binom {n}{k}}p^{k}(1-p)^{n-k}}$</td><td>${\\displaystyle np}$</td><th>${\\displaystyle np(1-p)}$</th></tr><tr><td>Geometric distribution</td><td>${\\displaystyle \\Pr \\,(X=k)=(1-p)^{k-1}p}$</td><td>${\\displaystyle {\\frac {1}{p}}}$</td><th>${\\displaystyle {\\frac {(1-p)}{p^{2}}}}$</th></tr><tr><td>Normal distribution</td><td>${\\displaystyle f\\left(x\\mid \\mu ,\\sigma ^{2}\\right)={\\frac {1}{\\sqrt {2\\pi \\sigma ^{2}}}}e^{-{\\frac {(x-\\mu )^{2}}{2\\sigma ^{2}}}}}$</td><td>${\\displaystyle \\mu }$</td><th>${\\displaystyle \\sigma ^{2}}$</th></tr><tr><td>Uniform distribution (continuous)</td><td>${\\displaystyle f(x\\mid a,b)={\\begin{cases}{\\frac {1}{b-a}}&{\\text{for }}a\\leq x\\leq b,\\\\[3pt]0&{\\text{for }}xb\\end{cases}}}$</td><td>${\\displaystyle {\\frac {a+b}{2}}}$</td><th>${\\displaystyle {\\frac {(b-a)^{2}}{12}}}$</th></tr><tr><td>Exponential distribution</td><td>${\\displaystyle f(x\\mid \\lambda )=\\lambda e^{-\\lambda x}}$</td><td>${\\displaystyle {\\frac {1}{\\lambda }}}$</td><th>${\\displaystyle {\\frac {1}{\\lambda ^{2}}}}$</th></tr><tr><td>Poisson distribution</td><td>${\\displaystyle f(k\\mid \\lambda )={\\frac {e^{-\\lambda }\\lambda ^{k}}{k!}}}$</td><td>${\\displaystyle \\lambda }$</td><th>${\\displaystyle \\lambda }$</th></tr></tbody></table>'
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            complex_table_tag = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')
            assert complex_table_tag[0].text == '<table><tbody><tr><th>Name of the probability distribution</th><th>Probability distribution function</th><th>Mean</th><th>Variance</th></tr><tr><td>Binomial distribution</td><td>${\\displaystyle \\Pr \\,(X=k)={\\binom {n}{k}}p^{k}(1-p)^{n-k}}$</td><td>${\\displaystyle np}$</td><th>${\\displaystyle np(1-p)}$</th></tr><tr><td>Geometric distribution</td><td>${\\displaystyle \\Pr \\,(X=k)=(1-p)^{k-1}p}$</td><td>${\\displaystyle {\\frac {1}{p}}}$</td><th>${\\displaystyle {\\frac {(1-p)}{p^{2}}}}$</th></tr><tr><td>Normal distribution</td><td>${\\displaystyle f\\left(x\\mid \\mu ,\\sigma ^{2}\\right)={\\frac {1}{\\sqrt {2\\pi \\sigma ^{2}}}}e^{-{\\frac {(x-\\mu )^{2}}{2\\sigma ^{2}}}}}$</td><td>${\\displaystyle \\mu }$</td><th>${\\displaystyle \\sigma ^{2}}$</th></tr><tr><td>Uniform distribution (continuous)</td><td>${\\displaystyle f(x\\mid a,b)={\\begin{cases}{\\frac {1}{b-a}}&{\\text{for }}a\\leq x\\leq b,\\\\[3pt]0&{\\text{for }}xb\\end{cases}}}$</td><td>${\\displaystyle {\\frac {a+b}{2}}}$</td><th>${\\displaystyle {\\frac {(b-a)^{2}}{12}}}$</th></tr><tr><td>Exponential distribution</td><td>${\\displaystyle f(x\\mid \\lambda )=\\lambda e^{-\\lambda x}}$</td><td>${\\displaystyle {\\frac {1}{\\lambda }}}$</td><th>${\\displaystyle {\\frac {1}{\\lambda ^{2}}}}$</th></tr><tr><td>Poisson distribution</td><td>${\\displaystyle f(k\\mid \\lambda )={\\frac {e^{-\\lambda }\\lambda ^{k}}{k!}}}$</td><td>${\\displaystyle \\lambda }$</td><th>${\\displaystyle \\lambda }$</th></tr></tbody></table>'

    def test_table_involve_after_code(self):
        """test table involve code, code被提取出去了，过滤掉空的和坏的table."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][10])
            base_url = 'https://en.m.wikipedia.org/wiki/Variance'
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            assert len(parts[0][0].xpath(f'.//{CCTag.CC_TABLE}')[0]) == 0

    @unittest.skip(reason='在code模块解决了table嵌套多行代码问题')
    def test_table_involve_code(self):
        """table involve code."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][11])
            base_url = 'https://en.m.wikipedia.org/wiki/Variance'
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            complex_table_tag = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')
            expect_path = base_dir.joinpath(test_case['expected'][3])
            content = open(expect_path, 'r', encoding='utf-8').read()
            assert complex_table_tag[0].text == content.strip('\n')

    @unittest.skip(reason='在code模块解决了这个问题')
    def test_table_involve_complex_code(self):
        """table involve complex code."""
        for test_case in TEST_CASES:
            raw_html_path = base_dir.joinpath(test_case['input'][12])
            base_url = 'https://en.m.wikipedia.org/wiki/Variance'
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
            complex_table_tag = parts[1][0].xpath(f'.//{CCTag.CC_TABLE}')
            expect_path = base_dir.joinpath(test_case['expected'][3])
            content = open(expect_path, 'r', encoding='utf-8').read()
            assert complex_table_tag[0].text == content.strip('\n')

    def test_nested_table1(self):
        """复杂嵌套表格."""
        raw_html_path = base_dir.joinpath('assets/recognizer/nested_table1.html')
        base_url = 'https://en.m.wikipedia.org/wiki/Variance'
        raw_html = raw_html_path.read_text(encoding='utf-8')
        parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
        assert len(parts) == 3
        content = parts[2][0].text_content()
        assert '<table><tr><td><table><tr><td><table><tr><td>Search APO</td></tr><tr><td>Advanced Search</td></tr></table></td></tr></table><table><tr><td></td><td>Home</td></tr><tr><td colspan="2"></td></tr><tr><td colspan="2">Browse</td></tr><tr><td></td><td>Communities\n\n& Collections</td></tr><tr><td></td><td>Issue Date</td></tr><tr><td></td><td>Author</td></tr><tr><td></td><td>Title</td></tr><tr><td></td><td>Subject</td></tr><tr><td colspan="2"></td></tr><tr><td colspan="2">Sign on to:</td></tr><tr><td></td><td>Receive email\n\nupdates</td></tr><tr><td></td><td>My APO\n\nauthorized users</td></tr><tr><td></td><td>Edit Profile</td></tr><tr><td colspan="2"></td></tr><tr><td></td><td>Help</td></tr><tr><td></td><td>About DSpace</td></tr></table></td><td>ANSTO Publications Online >\n\nJournal Publications >\n\nJournal Articles ><table><tr><td>Please use this identifier to cite or link to this item: http://apo.ansto.gov.au/dspace/handle/10238/2935</td></tr></table><table><tr><td>Title:</td><td>An investigation into transition metal ion binding properties of silk fibers and particles using radioisotopes.</td></tr><tr><td>Authors:</td><td>Rajkhowa, R\n\nNaik, R\n\nWang, L\n\nSmith, SV\n\nWang, X</td></tr><tr><td>Keywords:</td><td>Radioisotopes\n\nTransition Elements\n\nBinding Energy\n\nFibers\n\nAbsorption\n\nIons</td></tr><tr><td>Issue Date:</td><td>15-Mar-2011</td></tr><tr><td>Publisher:</td><td>Wiley-Blackwell</td>' in content

    def test_nested_table2(self):
        """复杂嵌套表格."""
        raw_html_path = base_dir.joinpath('assets/recognizer/nested_table2.html')
        base_url = 'https://en.m.wikipedia.org/wiki/Variance'
        raw_html = raw_html_path.read_text(encoding='utf-8')
        parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
        assert len(parts) == 2
        content = parts[1][0].text_content()
        assert '<table><tr><td colspan="2">jQuery(document).ready( function($) { if ($(\'#gateway-page\').length) { jQuery("body").addClass("fontyourface layout-one-sidebar layout-sidebar-first wide hff-43 pff-43 sff-43 slff-43 fixed-header-enabled slideout-side-right transparent-header-active path-node page-node-type-page"); }});\n\n.acalog-custom .region--light-typography.region--dark-background a {font-weight:normal;} .acalog-custom ul.icons-list {margin:0} .acalog-custom ul.icons-list li {margin:5px 12px 5px 0;} #gateway-footer-copyright {background:#f6f8f9; font-family:\'Libre Franklin\', Helvetica Neue, Arial, sans-serif; padding:20px;}\n\nwindow.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag(\'js\', new Date()); gtag(\'config\', \'G-L4J2WT8RM8\');\n\nMain Numbers:\n\n(615) 452-8600\n\n(888) 335-8722\n\nfacebook\n\ninstagram\n\ntwitter\n\nyoutube\n\nCampuses\n\nGallatin\n\nCookeville\n\nLivingston\n\nSpringfield\n\nAcademic Divisions\n\nBusiness & Technology\n\nHealth Sciences\n\nHumanities & Fine Arts\n\nMathematics & Science\n\nNursing\n\nSocial Science & Education\n\nResources\n\nAccreditation\n\nBookstore\n\nCampus Police\n\nContact Us\n\nEmployee Directory\n\nIT Help Desk\n\nLibrary\n\nMarketing & Communications</td></tr><tr><td></td><td>Volunteer State Community College</td></tr><tr><td></td><td><table><tr><td></td><td>May 24, 2024</td><td></td><td><table><tr><td>2013-2014 VSCC Catalog</td><td><table><tr><td>Select a Catalog\n\n2024-2025 Undergraduate Catalog\n\n2023-2024 Undergraduate Catalog [ARCHIVED CATALOG]\n\n2022-2023' in content

    def test_nested_table3(self):
        """复杂嵌套表格."""
        raw_html_path = base_dir.joinpath('assets/recognizer/nested_table3.html')
        base_url = 'https://en.m.wikipedia.org/wiki/Variance'
        raw_html = raw_html_path.read_text(encoding='utf-8')
        parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
        assert len(parts) == 3
        content = parts[2][0].text_content()
        assert "<table><tr><td><table><tr><td>What's New - Recent Content\n\nMembers' Peak Updates\n\nRecent Trip Reports\n\nRecent Trip Report Comments\n\nRecently added Images\n\nRecently added Peaks\n\nList Completers\n\nHeight List Completers\n\nElevation List Completers\n\nCounty Summit Completers\n\nWilderness Area Completers\n\nMember Profiles & Stats\n\nMember Profiles - Summary Stats\n\nMember Stats by Date Range & Charts\n\nCalendar Grid Completions\n\nPeaks Repeated\n\nMost Climbed Peaks\n\nUnclimbed Peaks\n\nUS Peak Totals by State\n\nMember Tools\n\nClosest 50 Peaks by Member\n\nClosest 50 Map\n\nClosest 50 List\n\nDownload your Peak List\n\nSearch Trip Reports\n\nUnclimbed by Custom Group\n\nExport CSV, GPX, POI, TOPO! Files\n\nElevation Threshold Progress Maps\n\nState Highest # Progress Maps\n\nCounty Summit Progress Maps\n\nStatewide County Summit Maps\n\nProminence Progress Maps\n\nState Quads Progress Maps\n\nQuadrangle Lookup\n\nDistance Calculator\n\nSlope Angle Calculator\n\nStats Category Leaders\n\nUS Highest 1,000 Peaks\n\nUS Highest 1,000 Member Area\n\n1,000 Highest Peak List\n\nUS Steepest 1,000 Peaks\n\nSteepness Member Area\n\nView 1,000 Steepest List\n\nUS 2,000' Prominence\n\nUS Prominence Member Area\n\nView US Prominence Peak Profiles\n\nView Member 5k Completion Maps\n\nProminence Progress Maps\n\nUS County Highpoints\n\nCounty Highpoints Member Area\n\nHighpoint Profiles - By State\n\nView Member's Completion Maps\n\nUS State Highpoints\n\nUS State Highpoints Member Area\n\nView State Highpoints List\n\nView Member's Completion Maps\n\nUS Wilderness Area Peaks\n\nWilderness Summits Member Area\n\nWilderness Area Detail by State" in content

    def test_nested_table4(self):
        """复杂嵌套表格."""
        raw_html_path = base_dir.joinpath('assets/recognizer/nested_table4.html')
        base_url = 'https://en.m.wikipedia.org/wiki/Variance'
        raw_html = raw_html_path.read_text(encoding='utf-8')
        parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
        assert len(parts) == 4
        content = parts[2][0].text_content()
        assert '<table><tr><td>Molecular line emissions from pre main sequence objects\n\nSaraceno, P. ; Benedettini, M. ; Caux, E. ; Ceccarelli, M. C. ; Clegg, P. E. ; Correia, J. C. ; di Giorgio, A. M. ; Giannini, T. ; Griffin, M. J. ; Leeks, S. J. ; Liseau, R. ; Lorenzetti, D. ; Molinari, S. ; Nisini, B. ; Smith, H. ; Spinoglio, L. ; Tomassi, E. and White, G. J. (1997). Molecular line emissions from pre main sequence objects. In: The first ISO workshop on Analytical Spectroscopy , 6-8 October 1997, Madrid, Spain, p. 291.\n\nFull text available as:<table><tr><td><table><tr><td>Preview</td></tr></table></td><td>PDF (Version of Record) - Requires a PDF viewer such asGSview ,Xpdf orAdobe Acrobat Reader\n\nDownload (239Kb)</td></tr></table><table><tr><th>URL:</th><td>http://cdsads.u-strasbg.fr/abs/1997ESASP.419..291S</td></tr><tr><th>Google Scholar:</th><td>Look up in Google Scholar</td></tr></table>Abstract\n\nWe present some preliminary results obtained with the LWS G.T. programme on the study of young objects driving molecular outflows. In particular, we discuss the importance of molecular emission in these sources and address the role of the H<sub>2</sub>0 cooling.<table><tr><th>Item Type:</th><td>Conference Item</td></tr><tr><th>Copyright Holders:</th><td>1997 European Space Agency</td></tr><tr><th>Extra Information:</th><td>Proceedings of the first ISO workshop on Analytical Spectroscopy, Madrid, Spain, 6-8 October 1997. Editors: A.M. Heras, K. Leech, N. R. Trams, and Michael Perry. Noordwijk, The Netherlands : ESA Publications Division, c1997. (ESA SP-419), 1997., pp.291-292</td></tr><tr><th>Academic Unit/Department:</th><td>Science > Physical Sciences</td></tr><tr><th>Interdisciplinary Research Centre:</th><td>Centre for Earth, Planetary, Space and Astronomical Research (CEPSAR)</td></tr><tr><th>Item ID:</th><td>32696</td></tr><tr><th>Depositing User:</th><td>Glenn White</td></tr>' in content

    def test_table_has_formula(self):
        """表格含有公式."""
        raw_html_path = base_dir.joinpath('assets/recognizer/table_has_formula.html')
        base_url = 'https://en.m.wikipedia.org/wiki/Variance'
        raw_html = raw_html_path.read_text(encoding='utf-8')
        parts = self.rec.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))], raw_html)
        assert parts[5][0].text_content() == '<table><thead><tr><th>Statistic</th><th># (units)</th></tr></thead><tbody><tr><td>Number of patients</td><td>11,000</td></tr><tr><td>Number of labeled beats</td><td>2,774,054,987</td></tr><tr><td>Sample rate</td><td>250Hz</td></tr><tr><td>Segment size</td><td>$2^{20}+1$= 1,048,577</td></tr><tr><td>Total number of segments</td><td>541,794 (not all patients have enough for 50 segments)</td></tr></tbody></table>'
