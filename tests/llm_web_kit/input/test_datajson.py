import copy
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_web_kit.exception.exception import (ExtractorChainInputException,
                                             MagicHtmlExtractorException)
from llm_web_kit.extractor.html.extractor import HTMLPageLayoutType
from llm_web_kit.input.datajson import (ContentList, DataJson, DataJsonKey,
                                        DataSourceCategory)
from llm_web_kit.libs.doc_element_type import DocElementType


class TestDataJsonInit(unittest.TestCase):
    def test_datajson_init(self):
        # Test empty initialization
        data = {}
        datajson = DataJson(data)
        assert isinstance(datajson.get_content_list(), ContentList)
        assert datajson.get_content_list().length() == 0

        # Test with content list
        data = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: 'html',
            DataJsonKey.CONTENT_LIST: [
                {'type': 'text', 'content': 'test content'}
            ]
        }
        datajson = DataJson(data)
        assert datajson.get_dataset_name() == 'test_dataset'
        assert datajson.get_file_format() == 'html'
        assert datajson.get_content_list().length() == 1

    def test_datajson_dict_operations(self):
        data = {
            'key1': 'value1',
            DataJsonKey.CONTENT_LIST: []
        }
        datajson = DataJson(data)

        # Test __getitem__
        assert datajson['key1'] == 'value1'

        # Test __setitem__
        datajson['key2'] = 'value2'
        assert datajson['key2'] == 'value2'

        # Test get() method
        assert datajson.get('key1') == 'value1'
        assert datajson.get('non_existent', 'default') == 'default'

        # Test __delitem__
        del datajson['key1']
        with pytest.raises(KeyError):
            _ = datajson['key1']

    def test_datajson_content_list_operations(self):
        data = {
            DataJsonKey.CONTENT_LIST: [
                {'type': 'text', 'content': 'content1'},
                {'type': 'code', 'content': 'code1'}
            ]
        }
        datajson = DataJson(data)
        content_list = datajson.get_content_list()

        # Test content list access
        assert content_list[0]['type'] == 'text'
        assert content_list[1]['content'] == 'code1'

        # Test content list modification
        content_list[0] = {'type': 'text', 'content': 'modified'}
        assert content_list[0]['content'] == 'modified'

        # Test content list append
        content_list.append({'type': 'image', 'content': 'image1'})
        assert content_list.length() == 3

    def test_datajson_serialization(self):
        data = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: 'html',
            DataJsonKey.CONTENT_LIST: [
                {'type': 'text', 'content': 'test content'}
            ]
        }
        datajson = DataJson(data)

        # Test to_dict()
        dict_data = datajson.to_dict()
        assert isinstance(dict_data, dict)
        assert dict_data[DataJsonKey.DATASET_NAME] == 'test_dataset'
        assert len(dict_data[DataJsonKey.CONTENT_LIST]) == 1

        # Test to_json()
        json_str = datajson.to_json()
        assert isinstance(json_str, str)
        assert 'test_dataset' in json_str
        assert 'test content' in json_str

    def test_datajson_validation(self):
        # Test invalid input type
        with pytest.raises(ExtractorChainInputException):
            DataJson([])  # List instead of dict

        # Test invalid content_list type
        with pytest.raises(ExtractorChainInputException):
            DataJson({DataJsonKey.CONTENT_LIST: 'invalid'})  # String instead of list

    def test_datajson_exclude_nodes_to_nlp_md(self):
        data = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: 'html',
            DataJsonKey.CONTENT_LIST: [[{
                'type': 'simple_table',
                'raw_content': "<table class=\"table itemDisplayTable\"><tr><td class=\"metadataFieldLabel dc_title\">Title: </td><td class=\"metadataFieldValue dc_title\">T.J. Byrne, Slide of floor plan, Poor Law Commission cottage, 1872.</td></tr><tr><td class=\"metadataFieldLabel dc_contributor\">Authors: </td><td class=\"metadataFieldValue dc_contributor\"><a class=\"author\" href=\"/browse?type=author&amp;value=T.J.%2C+Byrne\">T.J., Byrne</a><br><a class=\"author\" href=\"/browse?type=author&amp;value=Fewer%2C+Michael\">Fewer, Michael</a></td></tr><tr><td class=\"metadataFieldLabel dc_subject\">Keywords: </td><td class=\"metadataFieldValue dc_subject\">T.J. Byrne<br>Cottages<br>Poor Law Commission</td></tr><tr><td class=\"metadataFieldLabel dc_date_issued\">Issue Date: </td><td class=\"metadataFieldValue dc_date_issued\">2011<br>2011</td></tr><tr><td class=\"metadataFieldLabel dc_description\">Description: </td><td class=\"metadataFieldValue dc_description\">T.J. Byrne's slide of a one storey cottage, labelled 'Mr Barney's Plan', recommended by the Poor Law Commission, 1872.</td></tr><tr><td class=\"metadataFieldLabel dc_identifier_uri\">URI: </td><td class=\"metadataFieldValue dc_identifier_uri\"><a href=\"https://hdl.handle.net/10599/5719\">https://hdl.handle.net/10599/5719</a></td></tr><tr><td class=\"metadataFieldLabel\">Appears in Collections:</td><td class=\"metadataFieldValue\"><a href=\"/handle/10599/3\">Published Items</a><br><a href=\"/handle/10599/5553\">T.J. Byrne Collection</a><br></td></tr></table>",
                'content': {
                    'html': "<table><tr><td>Title:</td><td>T.J. Byrne, Slide of floor plan, Poor Law Commission cottage, 1872.</td></tr><tr><td>Authors:</td><td>T.J., Byrne Fewer, Michael</td></tr><tr><td>Keywords:</td><td>T.J. Byrne Cottages Poor Law Commission</td></tr><tr><td>Issue Date:</td><td>2011 2011</td></tr><tr><td>Description:</td><td>T.J. Byrne's slide of a one storey cottage, labelled 'Mr Barney's Plan', recommended by the Poor Law Commission, 1872.</td></tr><tr><td>URI:</td><td>https://hdl.handle.net/10599/5719</td></tr><tr><td>Appears in Collections:</td><td>Published Items T.J. Byrne Collection</td></tr></table>",
                    'is_complex': False,
                    'table_nest_level': '1'
                }
            }]]
        }
        datajson = DataJson(data)
        md = datajson.get_content_list().to_nlp_md(exclude_nodes=DocElementType.COMPLEX_TABLE)
        assert '<table>' not in md

    def test_datajson_exclude_nodes_to_mmd(self):
        data = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: 'html',
            DataJsonKey.CONTENT_LIST: [[{
                'type': 'simple_table',
                'raw_content': "<table class=\"table itemDisplayTable\"><tr><td class=\"metadataFieldLabel dc_title\">Title: </td><td class=\"metadataFieldValue dc_title\">T.J. Byrne, Slide of floor plan, Poor Law Commission cottage, 1872.</td></tr><tr><td class=\"metadataFieldLabel dc_contributor\">Authors: </td><td class=\"metadataFieldValue dc_contributor\"><a class=\"author\" href=\"/browse?type=author&amp;value=T.J.%2C+Byrne\">T.J., Byrne</a><br><a class=\"author\" href=\"/browse?type=author&amp;value=Fewer%2C+Michael\">Fewer, Michael</a></td></tr><tr><td class=\"metadataFieldLabel dc_subject\">Keywords: </td><td class=\"metadataFieldValue dc_subject\">T.J. Byrne<br>Cottages<br>Poor Law Commission</td></tr><tr><td class=\"metadataFieldLabel dc_date_issued\">Issue Date: </td><td class=\"metadataFieldValue dc_date_issued\">2011<br>2011</td></tr><tr><td class=\"metadataFieldLabel dc_description\">Description: </td><td class=\"metadataFieldValue dc_description\">T.J. Byrne's slide of a one storey cottage, labelled 'Mr Barney's Plan', recommended by the Poor Law Commission, 1872.</td></tr><tr><td class=\"metadataFieldLabel dc_identifier_uri\">URI: </td><td class=\"metadataFieldValue dc_identifier_uri\"><a href=\"https://hdl.handle.net/10599/5719\">https://hdl.handle.net/10599/5719</a></td></tr><tr><td class=\"metadataFieldLabel\">Appears in Collections:</td><td class=\"metadataFieldValue\"><a href=\"/handle/10599/3\">Published Items</a><br><a href=\"/handle/10599/5553\">T.J. Byrne Collection</a><br></td></tr></table>",
                'content': {
                    'html': "<table><tr><td>Title:</td><td>T.J. Byrne, Slide of floor plan, Poor Law Commission cottage, 1872.</td></tr><tr><td>Authors:</td><td>T.J., Byrne Fewer, Michael</td></tr><tr><td>Keywords:</td><td>T.J. Byrne Cottages Poor Law Commission</td></tr><tr><td>Issue Date:</td><td>2011 2011</td></tr><tr><td>Description:</td><td>T.J. Byrne's slide of a one storey cottage, labelled 'Mr Barney's Plan', recommended by the Poor Law Commission, 1872.</td></tr><tr><td>URI:</td><td>https://hdl.handle.net/10599/5719</td></tr><tr><td>Appears in Collections:</td><td>Published Items T.J. Byrne Collection</td></tr></table>",
                    'is_complex': False,
                    'table_nest_level': '1'
                }
            }, {
                'type': 'complex_table',
                'raw_content': "<table class=\"table itemDisplayTable\"><tr><td class=\"metadataFieldLabel dc_title\">Title: </td><td class=\"metadataFieldValue dc_title\">T.J. Byrne, Slide of floor plan, Poor Law Commission cottage, 1872.</td></tr><tr><td class=\"metadataFieldLabel dc_contributor\">Authors: </td><td class=\"metadataFieldValue dc_contributor\"><a class=\"author\" href=\"/browse?type=author&amp;value=T.J.%2C+Byrne\">T.J., Byrne</a><br><a class=\"author\" href=\"/browse?type=author&amp;value=Fewer%2C+Michael\">Fewer, Michael</a></td></tr><tr><td class=\"metadataFieldLabel dc_subject\">Keywords: </td><td class=\"metadataFieldValue dc_subject\">T.J. Byrne<br>Cottages<br>Poor Law Commission</td></tr><tr><td class=\"metadataFieldLabel dc_date_issued\">Issue Date: </td><td class=\"metadataFieldValue dc_date_issued\">2011<br>2011</td></tr><tr><td class=\"metadataFieldLabel dc_description\">Description: </td><td class=\"metadataFieldValue dc_description\">T.J. Byrne's slide of a one storey cottage, labelled 'Mr Barney's Plan', recommended by the Poor Law Commission, 1872.</td></tr><tr><td class=\"metadataFieldLabel dc_identifier_uri\">URI: </td><td class=\"metadataFieldValue dc_identifier_uri\"><a href=\"https://hdl.handle.net/10599/5719\">https://hdl.handle.net/10599/5719</a></td></tr><tr><td class=\"metadataFieldLabel\">Appears in Collections:</td><td class=\"metadataFieldValue\"><a href=\"/handle/10599/3\">Published Items</a><br><a href=\"/handle/10599/5553\">T.J. Byrne Collection</a><br></td></tr></table>",
                'content': {
                    'html': "<table><tr><td>Title:</td><td>T.J. Byrne, Slide of floor plan, Poor Law Commission cottage, 1872.</td></tr><tr><td>Authors:</td><td>T.J., Byrne Fewer, Michael</td></tr><tr><td>Keywords:</td><td>T.J. Byrne Cottages Poor Law Commission</td></tr><tr><td>Issue Date:</td><td>2011 2011</td></tr><tr><td>Description:</td><td>T.J. Byrne's slide of a one storey cottage, labelled 'Mr Barney's Plan', recommended by the Poor Law Commission, 1872.</td></tr><tr><td>URI:</td><td>https://hdl.handle.net/10599/5719</td></tr><tr><td>Appears in Collections:</td><td>Published Items T.J. Byrne Collection</td></tr></table>",
                    'is_complex': True,
                    'table_nest_level': '1'
                }
            }, {
                'type': 'image',
                'raw_content': "<img decoding=\"async\" loading=\"lazy\" aria-describedby=\"caption-attachment-17269\" class=\"wp-image-17269 size-full\" title=\"Curtindo o apartamento com piscina no centro de SP. \" src=\"https://naproadavida.com/wp-content/uploads/2020/11/20201024-Airbnb-SP-Consolacao_getaway_manha_Sony-1.jpg\" alt=\"Curtindo o apartamento com piscina no centro de SP. \" width=\"765\" height=\"510\" srcset=\"https://naproadavida.com/wp-content/uploads/2020/11/20201024-Airbnb-SP-Consolacao_getaway_manha_Sony-1.jpg 765w, https://naproadavida.com/wp-content/uploads/2020/11/20201024-Airbnb-SP-Consolacao_getaway_manha_Sony-1-480x320.jpg 480w\" sizes=\"(min-width: 0px) and (max-width: 480px) 480px, (min-width: 481px) 765px, 100vw\">",
                'content': {
                    'url': 'https://naproadavida.com/wp-content/uploads/2020/11/20201024-Airbnb-SP-Consolacao_getaway_manha_Sony-1.jpg',
                    'data': None,
                    'alt': 'Curtindo o apartamento com piscina no centro de SP. ',
                    'title': 'Curtindo o apartamento com piscina no centro de SP. ',
                    'caption': [],
                    'footnote': ['test image footnote']
                }
            }]]
        }
        datajson = DataJson(data)
        md = datajson.get_content_list().to_mm_md(exclude_nodes=DocElementType.COMPLEX_TABLE)
        assert '<table>' not in md
        assert 'Curtindo o apartamento com piscina no centro de SP.' in md

    def test_data_json_deepcopy(self):
        """从一个外部dict构建datajson, 改变datajson，不改变外部dict."""
        d = {'track_id': '32266dfa-c335-45c5-896e-56f057889d28',
             'url': 'http://mathematica.stackexchange.com/users/1931/ywdr1987?tab=activity&sort=all',
             'html': '',
             'page_layout_type': 'forum',
             'domain': 'mathematica.stackexchange.com',
             'dataset_name': 'math',
             'data_source_category': 'HTML',
             'meta_info': {'warc_headers': {'WARC-IP-Address': '104.16.12.13'}}}
        copied = copy.deepcopy(d)
        _ = DataJson(copied)
        cl = copied.get('content_list')  # 不该变外部变量d
        assert cl is None

    def test_datajson_to_dict_immutable(self):
        """测试to_dict()返回的dict修改不会影响原DataJson对象."""
        data = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: 'html',
            DataJsonKey.CONTENT_LIST: [
                {'type': 'text', 'content': 'test content'}
            ]
        }
        datajson = DataJson(data)

        # Get dict representation
        dict_data = datajson.to_dict()

        # Modify the returned dict
        dict_data[DataJsonKey.DATASET_NAME] = 'modified_dataset'
        dict_data[DataJsonKey.CONTENT_LIST][0]['content'] = 'modified content'

        # Original DataJson should remain unchanged
        assert datajson.get_dataset_name() == 'test_dataset'
        assert datajson.get_content_list()._get_data()[0]['content'] == 'test content'

        # Verify the modifications only affected the dict copy
        assert dict_data[DataJsonKey.DATASET_NAME] == 'modified_dataset'
        assert dict_data[DataJsonKey.CONTENT_LIST][0]['content'] == 'modified content'

    def test_data_json_to_nlp_md(self):
        d = {
            'track_id': '9fc6d25e-03ef-42a5-9675-7817c2b01936',
            'url': 'http://boards.fool.com/quoti-think-flegs-watching-what-he-eats-30294220.aspx?sort=username',
            'html': '',
            'content_list': [
                [
                    {
                        'type': 'paragraph',
                        'raw_content': '<div class=\"content\"><div class=\"description-wrapper\"><div class=\"container description\"><div class=\"report text-center\"><span class=\"text-muted\">\n\t\t\t\tZiet u iets wat niet hoort of niet klopt?\n\t\t\t</span></div></div></div></div>',
                        'content': [
                            {
                                'c': 'Ziet u iets wat niet hoort of niet klopt?',
                                't': 'text'
                            }
                        ]
                    },
                    {
                        'type': 'title',
                        'raw_content': '<h2 class=\"text-center \" data-step=\"4\">Openingstijden</h2>',
                        'content': {
                            'title_content': 'Openingstijden',
                            'level': '2'
                        }
                    },
                    {
                        'type': 'simple_table',
                        'raw_content': '<table class=\"table table-hover\" id=\"table-visitinghours\"><tr class=\"\"><td>\n\t\t\t\tMaandag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr><tr class=\"\"><td>\n\t\t\t\tDinsdag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr><tr class=\"\"><td>\n\t\t\t\tWoensdag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr><tr class=\"\"><td>\n\t\t\t\tDonderdag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr><tr class=\"\"><td>\n\t\t\t\tVrijdag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr><tr class=\"\"><td>\n\t\t\t\tZaterdag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr><tr class=\"\"><td>\n\t\t\t\tZondag\n\t\t\t</td><td class=\"text-right\">\n\n\t\t\t\t\t\t\t\t\t\t\t\t-\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t</td></tr></table>',
                        'content': {
                            'html': '<table><tr><td>Maandag</td><td>-</td></tr><tr><td>Dinsdag</td><td>-</td></tr><tr><td>Woensdag</td><td>-</td></tr><tr><td>Donderdag</td><td>-</td></tr><tr><td>Vrijdag</td><td>-</td></tr><tr><td>Zaterdag</td><td>-</td></tr><tr><td>Zondag</td><td>-</td></tr></table>',
                            'is_complex': False,
                            'table_nest_level': '1'
                        }
                    },
                    {
                        'type': 'code',
                        'raw_content': '<code>frame.open();\nframe.write(html);\nframe.close();\n</code>',
                        'inline': False,
                        'content': {
                            'code_content': 'frame.open();\nframe.write(html);\nframe.close();',
                            'by': 'tag_pre_code'
                        }
                    }
                ]
            ]
        }

        def test_default_exclude():
            datajson = DataJson(d)
            md = datajson.get_content_list().to_nlp_md()
            assert 'Ziet u iets wat niet hoort of niet klopt?' in md
            assert 'Openingstijden' in md
            assert 'Maandag' in md
            assert 'frame.open();\nframe.write(html);\nframe.close();' in md

        def test_custom_exclude():
            datajson = DataJson(d)
            md = datajson.get_content_list().to_nlp_md(
                exclude_nodes=[DocElementType.COMPLEX_TABLE, DocElementType.SIMPLE_TABLE])
            assert 'Ziet u iets wat niet hoort of niet klopt?' in md
            assert 'Openingstijden' in md
            assert 'Maandag' not in md
            assert 'frame.open();\nframe.write(html);\nframe.close();' in md

        test_default_exclude()
        test_custom_exclude()

    def test_to_txt_with_math_delimiters(self):
        """测试 to_txt 方法对数学公式分隔符的处理."""
        test_cases = [
            # 基本场景：单个公式
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '这是一个公式 [itex]x^2[/itex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '这是一个公式 $x^2$\n'
            },
            # 多个公式组合
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '行内公式 [itex]x^2[/itex] 和行间公式 [tex]y^3[/tex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '行内公式 $x^2$ 和行间公式 $$y^3$$\n'
            },
            # 多行文本中的公式
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '第一行文本\n包含公式 [itex]x^2[/itex]\n第三行文本\n包含公式 [tex]y^3[/tex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '第一行文本\n包含公式 $x^2$\n第三行文本\n包含公式 $$y^3$$\n'
            },
            # 多个段落
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '第一个段落 [itex]x^2[/itex]',
                                    't': 'text'
                                }
                            ]
                        },
                        {
                            'type': 'list',
                            'content': {
                                'items': [
                                    [
                                        [
                                            {
                                                'c': '第二个段落 [tex]y^3[/tex]',
                                                't': 'text'
                                            }
                                        ]
                                    ]
                                ],
                                'list_attribute': 'ordered',
                                'list_nest_level': 1,
                            }
                        }
                    ]]
                },
                'expected': '第一个段落 $x^2$\n1. 第二个段落 $$y^3$$\n'
            },
            # 复杂公式
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'list',
                            'content': {
                                'items': [
                                    [
                                        [
                                            {
                                                'c': '复杂公式 [tex]\\frac{x^2 + y^3}{z^4}[/tex] 和 [itex]\\sqrt{x^2 + y^2}[/itex]',
                                                't': 'text'
                                            }
                                        ]
                                    ]
                                ],
                                'list_attribute': 'ordered',
                                'list_nest_level': 1,
                            }
                        }
                    ]]
                },
                'expected': r'1. 复杂公式 $$\frac{x^2 + y^3}{z^4}$$ 和 $\sqrt{x^2 + y^2}$'
            }
        ]

        for case in test_cases:
            doc = DataJson(case['data'])
            result = doc.get_content_list().to_txt()
            assert result.strip() == case[
                'expected'].strip(), f"测试失败: 期望得到 '{case['expected']}' 但得到 '{result.strip()}'"

    def test_to_nlp_md_with_math_delimiters(self):
        """测试 to_nlp_md 方法对数学特殊公式分隔符的处理."""
        test_cases = [
            # 基本场景：单个公式
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '这是一个公式 [itex]x^2[/itex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '这是一个公式 $x^2$\n'
            },
            # 多个公式组合
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '行内公式 [itex]x^2[/itex] 和行间公式 [tex]y^3[/tex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '行内公式 $x^2$ 和行间公式 $$y^3$$\n'
            },
            # 多行文本中的公式
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '第一行文本\n包含公式 [itex]x^2[/itex]\n第三行文本\n包含公式 [tex]y^3[/tex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '第一行文本\n包含公式 $x^2$\n第三行文本\n包含公式 $$y^3$$\n'
            },
            # 多个段落
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '第一个段落 [itex]x^2[/itex]',
                                    't': 'text'
                                }
                            ]
                        },
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '第二个段落 [tex]y^3[/tex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '第一个段落 $x^2$\n\n第二个段落 $$y^3$$\n'
            },
            # 复杂公式
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'c': '复杂公式 [tex]\\frac{x^2 + y^3}{z^4}[/tex] 和 [itex]\\sqrt{x^2 + y^2}[/itex]',
                                    't': 'text'
                                }
                            ]
                        }
                    ]]
                },
                'expected': '复杂公式 $$\\frac{x^2 + y^3}{z^4}$$ 和 $\\sqrt{x^2 + y^2}$\n'
            },
            # 包含其他格式的文本
            {
                'data': {
                    'content_list': [[
                        {
                            'type': 'list',
                            'content': {
                                'items': [
                                    [
                                        [
                                            {
                                                'c': '**加粗文本** 和 *斜体文本* 中的公式 [itex]x^2[/itex]',
                                                't': 'text'
                                            }
                                        ]
                                    ]
                                ],
                                'list_attribute': 'ordered',
                                'list_nest_level': 1,
                            }
                        }
                    ]]
                },
                'expected': '1. **加粗文本** 和 *斜体文本* 中的公式 $x^2$\n'
            }
        ]

        for case in test_cases:
            doc = DataJson(case['data'])
            result = doc.get_content_list().to_nlp_md()
            assert result == case['expected'], f"测试失败: 期望得到 '{case['expected']}' 但得到 '{result}'"

    def test_to_plain_md(self):
        """测试to_plain_md方法调用."""
        from llm_web_kit.libs.standard_utils import json_loads
        from llm_web_kit.simple import (
            extract_content_from_html_with_layout_batch,
            extract_content_from_html_with_llm,
            extract_content_from_html_with_magic_html,
            extract_content_from_main_html)

        base_dir = Path(__file__).parent
        raw_html = base_dir.joinpath('assets/to_plain_md.html').read_text(encoding='utf-8')
        url = 'http://example.com'

        plain_md = extract_content_from_html_with_magic_html(url, raw_html, 'plain_md')
        mm_md = extract_content_from_html_with_magic_html(url, raw_html, 'mm_md')
        json_json = json_loads(extract_content_from_html_with_magic_html(url, raw_html, 'json'))

        self.assertNotIn('code.language', plain_md)
        self.assertNotIn('Private Sub sitemenu_ItemCreated', plain_md)
        self.assertNotIn('<table>', plain_md)
        self.assertNotIn('a^2', plain_md)
        self.assertNotIn('x=4', plain_md)
        self.assertNotIn('image', plain_md)
        self.assertNotIn('test.mp3', plain_md)
        self.assertNotIn('flower.mp4', plain_md)

        self.assertIn('Title Test', plain_md)
        self.assertIn('1.1', plain_md)
        self.assertIn('UL1.1', plain_md)
        self.assertIn('test paragraph', plain_md)

        self.assertIn('code.language', mm_md)
        self.assertIn('Private Sub sitemenu_ItemCreated', mm_md)
        self.assertIn('<table>', mm_md)
        self.assertIn('a^2', mm_md)
        self.assertIn('x=4', mm_md)
        self.assertIn('image', mm_md)
        self.assertNotIn('test.mp3', mm_md)
        self.assertNotIn('flower.mp4', mm_md)

        content_json = json_loads(base_dir.joinpath('assets/content_json.json').read_text(encoding='utf-8'))
        self.assertEqual(json_json['content_list'], content_json['content_list'])

        plain_md_main = extract_content_from_main_html(url, raw_html, 'plain_md')
        mm_md_main = extract_content_from_html_with_magic_html(url, raw_html, 'mm_md')
        json_main = json_loads(extract_content_from_html_with_magic_html(url, raw_html, 'json'))

        self.assertNotIn('code.language', plain_md_main)
        self.assertNotIn('Private Sub sitemenu_ItemCreated', plain_md_main)
        self.assertNotIn('<table>', plain_md_main)
        self.assertNotIn('a^2', plain_md_main)
        self.assertNotIn('x=4', plain_md_main)
        self.assertNotIn('image', plain_md_main)
        self.assertNotIn('test.mp3', plain_md_main)
        self.assertNotIn('flower.mp4', plain_md_main)

        self.assertIn('Title Test', plain_md_main)
        self.assertIn('1.1', plain_md_main)
        self.assertIn('UL1.1', plain_md_main)
        self.assertIn('test paragraph', plain_md_main)

        self.assertIn('code.language', mm_md_main)
        self.assertIn('Private Sub sitemenu_ItemCreated', mm_md_main)
        self.assertIn('<table>', mm_md_main)
        self.assertIn('a^2', mm_md_main)
        self.assertIn('x=4', mm_md_main)
        self.assertIn('image', mm_md_main)
        self.assertNotIn('test.mp3', mm_md_main)
        self.assertNotIn('flower.mp4', mm_md_main)

        self.assertEqual(json_main['content_list'], content_json['content_list'])

        plain_md_llm = extract_content_from_html_with_llm(url, raw_html, 'plain_md')
        mm_md_llm = extract_content_from_html_with_magic_html(url, raw_html, 'mm_md')
        json_llm = json_loads(extract_content_from_html_with_magic_html(url, raw_html, 'json'))

        self.assertNotIn('code.language', plain_md_llm)
        self.assertNotIn('Private Sub sitemenu_ItemCreated', plain_md_llm)
        self.assertNotIn('<table>', plain_md_llm)
        self.assertNotIn('a^2', plain_md_llm)
        self.assertNotIn('x=4', plain_md_llm)
        self.assertNotIn('image', plain_md_llm)
        self.assertNotIn('test.mp3', plain_md_llm)
        self.assertNotIn('flower.mp4', plain_md_llm)

        self.assertIn('Title Test', plain_md_llm)
        self.assertIn('1.1', plain_md_llm)
        self.assertIn('UL1.1', plain_md_llm)
        self.assertIn('test paragraph', plain_md_llm)

        self.assertIn('code.language', mm_md_llm)
        self.assertIn('Private Sub sitemenu_ItemCreated', mm_md_llm)
        self.assertIn('<table>', mm_md_llm)
        self.assertIn('a^2', mm_md_llm)
        self.assertIn('x=4', mm_md_llm)
        self.assertIn('image', mm_md_llm)
        self.assertNotIn('test.mp3', mm_md_llm)
        self.assertNotIn('flower.mp4', mm_md_llm)

        self.assertEqual(json_llm['content_list'], content_json['content_list'])

        plain_md_layout = extract_content_from_html_with_layout_batch(url, raw_html, 'plain_md')
        mm_md_layout = extract_content_from_html_with_magic_html(url, raw_html, 'mm_md')
        json_layout = json_loads(extract_content_from_html_with_magic_html(url, raw_html, 'json'))

        self.assertNotIn('code.language', plain_md_layout)
        self.assertNotIn('Private Sub sitemenu_ItemCreated', plain_md_layout)
        self.assertNotIn('<table>', plain_md_layout)
        self.assertNotIn('a^2', plain_md_layout)
        self.assertNotIn('x=4', plain_md_layout)
        self.assertNotIn('image', plain_md_layout)
        self.assertNotIn('test.mp3', plain_md_layout)
        self.assertNotIn('flower.mp4', plain_md_layout)

        self.assertIn('Title Test', plain_md_layout)
        self.assertIn('1.1', plain_md_layout)
        self.assertIn('UL1.1', plain_md_layout)
        self.assertIn('test paragraph', plain_md_layout)

        self.assertIn('code.language', mm_md_layout)
        self.assertIn('Private Sub sitemenu_ItemCreated', mm_md_layout)
        self.assertIn('<table>', mm_md_layout)
        self.assertIn('a^2', mm_md_layout)
        self.assertIn('x=4', mm_md_layout)
        self.assertIn('image', mm_md_layout)
        self.assertNotIn('test.mp3', mm_md_layout)
        self.assertNotIn('flower.mp4', mm_md_layout)

        self.assertEqual(json_layout['content_list'], content_json['content_list'])


class TestDataJsonGetMagicHtml:
    base_dir = Path(__file__).parent

    test_cases = [
        {
            'input': (
                'assets/html/magic_main_html_input.html',
                'http://plainblogaboutpolitics.blogspot.com/2011/12/acceptable.html?m=1'
            ),
            'expected': [
                'assets/output_expected/magic_main_html_output.html'
            ]
        }
    ]

    def setup_method(self):
        sample_case_one = self.test_cases[0]
        raw_html_path = self.base_dir.joinpath(sample_case_one['input'][0])

        self.data = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: DataSourceCategory.HTML,
            'html': raw_html_path.read_text(),
            'url': sample_case_one['input'][1]
        }
        self.data_json = DataJson(self.data)

    def test_get_magic_html_success(self):
        # Mock the extract_magic_html function to return a known response
        expected_html_path = self.base_dir.joinpath(self.test_cases[0]['expected'][0])
        expected_html = expected_html_path.read_text() if expected_html_path.exists() else "<div class='main'>Test Content</div>"

        with patch('llm_web_kit.libs.html_utils.extract_magic_html') as mock_extractor:
            mock_extractor.return_value = expected_html

            # Call the method being tested
            result = self.data_json.get_magic_html()

            # Verify the result
            assert result == expected_html

            # Verify the extractor was called with correct arguments
            mock_extractor.assert_called_once_with(
                self.data['html'],
                self.data['url'],
                HTMLPageLayoutType.LAYOUT_ARTICLE
            )

    def test_get_magic_html_error_handling(self):
        # Test error handling
        with patch('llm_web_kit.libs.html_utils.extract_magic_html') as mock_extractor:
            mock_extractor.side_effect = MagicHtmlExtractorException('Test error')

            # Verify that the appropriate exception is raised
            with pytest.raises(MagicHtmlExtractorException) as excinfo:
                self.data_json.get_magic_html()

            # Check the error message
            assert 'Test error' in str(excinfo.value)

    def test_get_magic_html_missing_html(self):
        # Test with missing HTML content
        data_without_html = {
            DataJsonKey.DATASET_NAME: 'test_dataset',
            DataJsonKey.FILE_FORMAT: DataSourceCategory.HTML,
            'url': self.data['url']
        }
        data_json = DataJson(data_without_html)

        with patch('llm_web_kit.libs.html_utils.extract_magic_html') as mock_extractor:
            mock_extractor.return_value = ''

            # Should work with None HTML
            result = data_json.get_magic_html()
            assert result == ''

            mock_extractor.assert_called_once_with(
                None,
                self.data['url'],
                HTMLPageLayoutType.LAYOUT_ARTICLE
            )
