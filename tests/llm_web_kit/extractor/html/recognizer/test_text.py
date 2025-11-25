# 测试text识别器
import os
import unittest
from pathlib import Path

from llm_web_kit.config.cfg_reader import load_pipe_tpl
from llm_web_kit.extractor.extractor_chain import ExtractSimpleFactory
from llm_web_kit.extractor.html.recognizer.recognizer import \
    BaseHTMLElementRecognizer
from llm_web_kit.extractor.html.recognizer.text import TextParagraphRecognizer
from llm_web_kit.input.datajson import DataJson
from llm_web_kit.libs.html_utils import (element_to_html_unescaped,
                                         html_to_element)


class TestTextParagraphRecognize(unittest.TestCase):
    def setUp(self):
        self.text_recognize = TextParagraphRecognizer()
        # Config for HTML extraction
        self.config = load_pipe_tpl('html-test')

    def test_text_1(self):
        """
        测试1  s3://llm-pdf-text-1/qa/quyuan/output/part-67c01310620e-000064.jsonl
        Returns:

        """
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/assets/recognizer/text.html', 'r') as file:
            html_content = file.read()
        assert self.text_recognize._TextParagraphRecognizer__combine_text('知识乱象\n',
                                                                          '中共中央政治局召开会议审议《成-2020年10月16日新闻联播',
                                                                          'zh') == '知识乱象\n中共中央政治局召开会议审议《成-2020年10月16日新闻联播'
        result = self.text_recognize.recognize('http://www.baidu.com', [(html_to_element(html_content), html_to_element(html_content))], html_content)
        assert '知识乱象\\n 中共中央政治局' in element_to_html_unescaped(result[587][0])

    def test_text_2(self):
        """
        测试2  s3://llm-pdf-text-1/qa/quyuan/output/part-67c01310620e-004720.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://www.aircraftspruce.com/catalog/pnpages/AT108AR-5_32.php',
            'data_source_category': 'HTML',
            'path': 'text2.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'Selecting Rivet Sets:\n To develop maximum power' in content_md

    def test_text_3(self):
        """
        测试3  s3://llm-pdf-text-1/qa/quyuan/mathout/part-67c05902108f-001066.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://www.physicsforums.com/threads/how-do-convex-mirrors-affect-image-location-and-size.240850/',
            'data_source_category': 'HTML',
            'path': 'text3.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert "1. The problem statement, all variables and given/known data\n A woman of height 1.7 meters stands directly in front of a convex mirror 2.0 meters away. The mirror has a radius of curvature, R=-50cm. Find the location and size of a woman's image using the ray diagram and mirror/lens equation.\n\n----------\n\n 2. The speed of light in a material is 2.50x10^8 meters per second. What is the index of refraction of the material?\n\n 2. Relevant equations\n\n 3. The attempt at a solution\n 1. di=22.22\n\n 2. Dont know" in content_md

    def test_text_4(self):
        """
        测试4  s3://llm-pdf-text-1/qa/quyuan/mathout/part-67c05902108f-000050.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://www.physicsforums.com/threads/isnt-the-normal-acceleration-always-towards-the-center.157291/',
            'data_source_category': 'HTML',
            'path': 'text4.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '1. The problem statement, all variables and given/known data\n 2. Relevant equations\n\n See attachment\n\n 3. The attempt at a solution\n I solved the problem' in content_md

    def test_text_5(self):
        """
        测试5  s3://llm-pdf-text-1/qa/quyuan/output/part-67c01310620e-007988.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://shopnado.com.au/product/rigo-ride-on-car-tractor-toy-kids-electric-cars-12v-battery-child-toddlers-blue/',
            'data_source_category': 'HTML',
            'path': 'text5.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'Please Note:\n 1. Charge the battery on receiving even if it will not be used soon.\n 2. Charge the battery EVERY MONTH if not in use for long periods to prevent over-discharging of the battery. This can cause irreparable damage to it.' in content_md

    def test_text_6(self):
        """
        测试6  s3://llm-pdf-text-1/qa/quyuan/output/part-67c01310620e-012288.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://adelanta.biz/kuplu-knigi/the-experience-of-russian-bibliography-copikova-part-2-l/',
            'data_source_category': 'HTML',
            'path': 'text6.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '1813 года\n\n5864. Лабиринт волшебства, или удивительные приключения восточных принцев, сочинение В. Протопоповича; Москва, 1786 г. - в 8°.\n\n 5865. Лакировальщик' in content_md

    def test_text_7(self):
        """
        测试7  s3://llm-pdf-text-1/qa/quyuan/mathout/part-67c05902108f-001871.jsonl
        ps：badcase未保留行是因为走的cc
        Returns:

        """
        with open(Path(__file__).parent.parent.parent / 'assets/extractor_chain_input/good_data/html/text7.html', 'r') as file:
            html_content = file.read()
        result = self.text_recognize.recognize('http://www.baidu.com', [(html_to_element(html_content), html_to_element(html_content))], html_content)
        assert '1) A man takes 5 hrs and 45 mins to walk to a certain place and ride back' in element_to_html_unescaped(result[66][0]) and BaseHTMLElementRecognizer.is_cc_html(result[66][0])

    def test_text_8(self):
        """
        测试8  s3://llm-pdf-text-1/qa/quyuan/mathout/part-67c05902108f-001477.jsonl
        ps：badcase未保留行是因为走的cc
        Returns:

        """
        with open(Path(__file__).parent.parent.parent / 'assets/extractor_chain_input/good_data/html/text8.html', 'r') as file:
            html_content = file.read()
        result = self.text_recognize.recognize('http://www.baidu.com', [(html_to_element(html_content), html_to_element(html_content))], html_content)
        assert "40xy\' -ln(x^8) = 0\\n\\n Initial Condition: y(1)=31\\n\\n Work:" in element_to_html_unescaped(result[69][0]) and BaseHTMLElementRecognizer.is_cc_html(result[69][0])

    def test_text_9(self):
        """
        测试9  s3://llm-pdf-text-1/qa/quyuan/mathout/part-67c05902108f-000073.jsonl
        ps：badcase未保留行是因为走的cc
        Returns:

        """
        with open(Path(__file__).parent.parent.parent / 'assets/extractor_chain_input/good_data/html/text9.html', 'r') as file:
            html_content = file.read()
        result = self.text_recognize.recognize('http://www.baidu.com', [(html_to_element(html_content), html_to_element(html_content))], html_content)
        assert '1) Consider the formula f(x)=lim(n--&gt;infinity)((x^n)/(1+x^n)).\\n Let D={x:f(x) is an element of R}. Calculate f(x) for all x elements of D and determine where f: D--&gt;R is continuous.\\n\\n 2) Let f: D--&gt;R and suppose that f(x) greater than equal 0 for all x elements of D. Define sqrt(f)--&gt;R by (sqrt(f))(x) = sqrt(f(x)). If f is continuous at c elements of D, prove that sqrt(f) is continuous at c.' in element_to_html_unescaped(result[63][0]) and BaseHTMLElementRecognizer.is_cc_html(result[63][0])

    def test_text_10(self):
        """
        测试10  s3://llm-pdf-text-1/qa/quyuan/mathout/part-67c05902108f-000620.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://www.physicsforums.com/threads/questions-about-parallel-worlds-by-michio-kaku-the-big-bang.612643/',
            'data_source_category': 'HTML',
            'path': 'text10.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'So far I have 2 sets of questions (but I\'m onlin in the 2nd chapter now\n\n![:smile:](d80757e36ca9835f7237339959a1fa1d929bb5c5297acb457475459d6da12278 "Smile    :smile:")\n\n)\n\n 1)\n In the book' in content_md

    def test_text_11(self):
        """
        测试11  s3://web-parse-huawei/CC/pre-dedup/v008/unique_html/CC-MAIN-2013-48/part-67a0f2d36291-000157.jsonl.gz?bytes=47048276,27451
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'http://community.wikia.com/wiki/Help_talk:Theme_designer',
            'data_source_category': 'HTML',
            'path': 'text11.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '86,821 pages on' in content_md

    def test_text_12(self):
        """
        测试11  s3://llm-pdf-text-1/qa/quyuan/CC3.0/v009/data/part-67e685f42e4c-000000.jsonl?bytes=101642,27293
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://betterexplained.com/~kazad/resources/shorts/karate_old.html',
            'data_source_category': 'HTML',
            'path': 'text12.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'For maintaining mount' in content_md

    def test_text_line_exception(self):
        """
        测试13  s3://xyz-llm-users/xyz-users/minrui/layout_benchmark/sample/v005/label/188b8435-3150-455c-8159-096c41ef3926.jsonl
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://www.oltrelebarriere.net/5825/permessi-per-lassistenza-ai-familiari-disabili/',
            'data_source_category': 'HTML',
            'path': 'test_text_line_exception.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'}
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'sensi dell’art.33' in content_md

    def test_no_separation_language(self):
        """
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://www.zjfish.org/Talent/Detail/876289162604750/2174994673059649',
            'data_source_category': 'HTML',
            'path': 'zh.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'zh'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '成果； 三' not in content_md

    def test_tail_space(self):
        """
        Returns:

        """
        chain = ExtractSimpleFactory.create(self.config)
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'br.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'br'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'Henañ (c' in content_md

    def test_interactive_element(self):
        """
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'delete_interactive_element1.html',
            'main_path': 'delete_interactive_element1_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        # 验证 main_html 中没有交互元素
        main_html = result.get('main_html')
        assert '<input' not in main_html

    def test_normalize_space1(self):
        """
        测试换行不正确
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'text_normalize_space1.html',
            'main_path': 'text_normalize_space1_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'Please note! These' in content_md

    def test_normalize_space2(self):
        """
        测试换行不正确
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'text_normalize_space2.html',
            'main_path': 'text_normalize_space2_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'December 10th 2009, 06:42 PM\nfearless901\nCan someone please tell me my code wont work, error after error\nim need to write code to get height and time of the fluid in a reservoir, help guys. is my functions wrong?\nCode' in content_md

    def test_normalize_space3(self):
        """
        测试换行不正确
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'text_normalize_space3.html',
            'main_path': 'text_normalize_space3_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '### Volume 6, Issue 3, 01 February 1965\n\n- INFRARED LASER ACTION AND LIFETIMES IN ARGON II\nF. A. Horrigan , S. H. Koozekanani and R. A. Paananen\nScitation Author Page\nPubMed\nGoogle Scholar\nSource' in content_md

    def test_normalize_space4(self):
        """
        测试换行不正确
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'text_normalize_space4.html',
            'main_path': 'text_normalize_space4_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert '1. DrDu\nLieber Hendrik,\nkannst Du hierzu was beitragen?\nIch finde keinen rechten Grund'
        assert 'Show Ignored Content' not in content_md  # 这个是隐藏标签，不应该被识别出来

    def test_Lack_content1(self):
        """
        测试换缺少内容
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'Lack_content1.html',
            'main_path': 'Lack_content1_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'a) Electronic mail: airegg.py90g@nctu.edu.tw .' in content_md

    def test_para_br(self):
        """
        测试修复段落结尾为\n\n
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'para_br.html',
            'main_path': 'para_br_main.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert 'The interquartile range formula is the first quartile subtracted from the third quartile:\n $IQR = Q_{3}-Q_{1}' in content_md

    def test_para_has_none(self):
        """
        兼容段落可能为None的情况
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'para_has_none.html',
            'main_path': 'para_has_none.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert content_md

    def test_clean_invisible_elements(self):
        """
        清理隐藏标签
        Returns:

        """
        chain = ExtractSimpleFactory.create(load_pipe_tpl('noclip_html_test'))
        self.assertIsNotNone(chain)
        test_data = {
            'track_id': 'text_md',
            'dataset_name': 'text_md',
            'url': 'https://br.wikipedia.org/wiki/Faustina_an_Hena%C3%B1',
            'data_source_category': 'HTML',
            'path': 'clean_invisible_elements.html',
            'main_path': 'clean_invisible_elements.html',
            'file_bytes': 1000,
            'meta_info': {'input_datetime': '2020-01-01 00:00:00'},
            'language': 'en'
        }
        input_data = DataJson(test_data)
        result = chain.extract(input_data)
        content_md = result.get_content_list().to_mm_md()
        assert "Choosing a selection results in a full page refresh." not in content_md

    def test_empty_string_fix(self):
        """
        测试修复字符串索引越界问题 - 当文本处理中出现空字符串时不应抛出IndexError
        这个测试验证了__combine_text方法能够正确处理空字符串的情况
        """
        # 直接测试__combine_text方法处理空字符串的能力
        text_recognizer = TextParagraphRecognizer()

        # 测试各种空字符串组合
        result1 = text_recognizer._TextParagraphRecognizer__combine_text('hello', '', 'en')
        self.assertEqual(result1, 'hello')

        result2 = text_recognizer._TextParagraphRecognizer__combine_text('', 'world', 'en')
        self.assertEqual(result2, 'world')

        result3 = text_recognizer._TextParagraphRecognizer__combine_text('', '', 'en')
        self.assertEqual(result3, '')

        # 测试包含空格但trim后变空的情况
        result4 = text_recognizer._TextParagraphRecognizer__combine_text('hello', '   ', 'en')
        self.assertEqual(result4, 'hello')

        result5 = text_recognizer._TextParagraphRecognizer__combine_text('   ', 'world', 'en')
        self.assertEqual(result5, 'world')

        # 测试正常情况仍然工作
        result6 = text_recognizer._TextParagraphRecognizer__combine_text('hello', 'world', 'en')
        self.assertEqual(result6, 'hello world')

        # 测试标点符号情况
        result7 = text_recognizer._TextParagraphRecognizer__combine_text('hello', ',world', 'en')
        self.assertEqual(result7, 'hello,world')
