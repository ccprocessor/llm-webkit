import unittest
from pathlib import Path

from llm_web_kit.extractor.html.recognizer.image import ImageRecognizer
from llm_web_kit.extractor.html.recognizer.recognizer import CCTag
from llm_web_kit.libs.html_utils import element_to_html, html_to_element

TEST_CASES_HTML = [
    {
        'input': 'assets/ccimage/figure_iframe.html',
        'base_url': 'http://15.demooo.pl/produkt/okulary-ochronne/',
        'expected': 33,
        'ccimg_html': """<html lang="pl-PL" prefix="og: https://ogp.me/ns#"><body class="product-template-default single single-product postid-2386 theme-starter woocommerce woocommerce-page woocommerce-no-js tinvwl-theme-style"><header class="Header bg-white py-8 lg:py-0 sticky lg:fixed lg:w-full left-0 top-0 transition-all duration-300 z-50"><div class="Container flex justify-between items-center"><div class="Header__logo"><a href="http://15.demooo.pl"><ccimage by="img" html=\'&lt;img src="http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg" alt="Janser Logo"&gt;\' format="url" alt="Janser Logo">http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg</ccimage></a></div></div></header></body></html>"""
    },
    {
        'input': 'assets/ccimage/picture_img.html',
        'base_url': 'http://yuqiaoli.cn/Shop/List_249.html',
        'expected': 53,
        'ccimg_html': """<html lang="en"><body><div id="page_container"><div id="header_nav"><header><div id="header" class="table"><section id="logo" class="tablecell"><div id="header_logo"><a href="https://www.bonty.net/"><ccimage by="img" html=\'&lt;img src="https://www.bonty.net/templates/darkmode/images/logo.webp?v=Y2024M07D12" width="180" height="180" alt="bonty" id="header_logo_img"&gt;\' format="url" alt="bonty" width="180" height="180">https://www.bonty.net/templates/darkmode/images/logo.webp?v=Y2024M07D12</ccimage></a></div></section></div></header></div></div></body></html>"""
    },
    {
        'input': 'assets/ccimage/svg_base64.html',
        'base_url': 'https://www.terrasoleil.com/collections/bestsellers/products/luna-soleil-tarot-deck',
        'expected': 179,
        'ccimg_html': """<html class="no-js" lang="en"><body><ccimage by="img" html=\'&lt;img alt="icon" width="9999" height="9999" style="pointer-events: none; position: absolute; top: 0; left: 0; width: 99vw; height: 99vh; max-width: 100%; max-height: 100%;" src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIHdpZHRoPSI5OTk5OXB4IiBoZWlnaHQ9Ijk5OTk5cHgiIHZpZXdCb3g9IjAgMCA5OTk5OSA5OTk5OSIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIj48ZyBzdHJva2U9Im5vbmUiIGZpbGw9Im5vbmUiIGZpbGwtb3BhY2l0eT0iMCI+PHJlY3QgeD0iMCIgeT0iMCIgd2lkdGg9Ijk5OTk5IiBoZWlnaHQ9Ijk5OTk5Ij48L3JlY3Q+IDwvZz4gPC9zdmc+"&gt;\n \' format="base64" alt="icon" width="9999" height="9999">data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIHdpZHRoPSI5OTk5OXB4IiBoZWlnaHQ9Ijk5OTk5cHgiIHZpZXdCb3g9IjAgMCA5OTk5OSA5OTk5OSIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIj48ZyBzdHJva2U9Im5vbmUiIGZpbGw9Im5vbmUiIGZpbGwtb3BhY2l0eT0iMCI+PHJlY3QgeD0iMCIgeT0iMCIgd2lkdGg9Ijk5OTk5IiBoZWlnaHQ9Ijk5OTk5Ij48L3JlY3Q+IDwvZz4gPC9zdmc+</ccimage></body></html>"""
    },
    {
        'input': 'assets/ccimage/svg_img.html',
        'base_url': 'https://villarichic.com/collections/dresses/products/dont-hang-up-faux-suede-shirt-dress1?variant=45860191863029',
        'expected': 32,
        'ccimg_html': """<html lang="en" class="no-js"><body class="gridlock template-product product theme-features__header-border-style--solid theme-features__header-horizontal-alignment--bottom theme-features__header-border-weight--3 theme-features__header-border-width--10 theme-features__header-edges--none theme-features__h2-size--28 theme-features__header-vertical-alignment--center theme-features__rounded-buttons--enabled theme-features__display-options--image-switch theme-features__product-align--center theme-features__product-border--disabled theme-features__product-info--sizes theme-features__price-bold--disabled theme-features__product-icon-position--top-left theme-features__ultra-wide--disabled js-slideout-toggle-wrapper js-modal-toggle-wrapper"><main id="main-content" class="site-wrap" role="main" tabindex="-1"><div class="js-header-group"><div id="shopify-section-sections--18000509272309__header" class="shopify-section shopify-section-group-header-group js-site-header"><theme-header><header class="header__wrapper  above_center js-theme-header stickynav" data-section-id="sections--18000509272309__header" data-section-type="header-section" data-overlay-header-enabled="false"><nav class="header__nav-container   bottom-border js-nav"><div class="header__nav-above grid__wrapper  device-hide"><div class="span-6 push-3 a-center v-center"><div id="logo" class="header__logo-image"><a href="/"><ccimage by="img" html=\'&lt;img src="//villarichic.com/cdn/shop/files/Dark_Blue_Villari_Chic_Logo.png?v=1725465655&amp;amp;width=600" alt="" srcset="//villarichic.com/cdn/shop/files/Dark_Blue_Villari_Chic_Logo.png?v=1725465655&amp;amp;width=352 352w, //villarichic.com/cdn/shop/files/Dark_Blue_Villari_Chic_Logo.png?v=1725465655&amp;amp;width=600 600w" width="600" height="106" loading="eager" fetchpriority="high"&gt;\n                                    \' format="url" width="600" height="106">https://villarichic.com/cdn/shop/files/Dark_Blue_Villari_Chic_Logo.png?v=1725465655&amp;width=600</ccimage></a></div></div></div></nav></header></theme-header></div></div></main></body></html>"""
    },
    {
        'input': 'assets/ccimage/table_img.html',
        'base_url': 'http://www.99ja.cn/products/product-86-401.html',
        'expected': 1,
    },
    {
        'input': 'assets/ccimage/unescape_img.html',
        'base_url': 'http://www.aspengreencbd.net/category.php?id=47',
        'expected': 28,
        'ccimg_html': """<html xmlns="http://www.w3.org/1999/xhtml"><body><div class="header-main"><div class="block"><div class="header-logo header-logo-index"><a href="index.php"><ccimage by="img" html=\'&lt;img src="themes/ecmoban_kaola2016/images/logo.gif" alt=""&gt;\' format="url">http://www.aspengreencbd.net/themes/ecmoban_kaola2016/images/logo.gif</ccimage></a></div></div></div></body></html>"""
    },
    {
        'input': 'assets/ccimage/no_parent_img.html',
        'base_url': 'https://orenburg.shtaketniki.ru/evroshtaketnik-uzkij.html',
        'expected': 2,
        'ccimg_html': """<htmllang="ru"><body><ccimageby="img"html=\'&lt;imgclass="lazyload"data-src="/work/img/Screenshot_608.png"src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="title="Видеозаборовизметаллоштакетника"alt="Видеозаборовизметаллоштакетника"&gt;\'format="url"alt="В идеозаборовизметаллоштакетника"title="Видеозаборовизметаллоштакетника">https://orenburg.shtaketniki.ru/work/img/Screenshot_608.png</ccimage></body></html>"""
    },
    {
        'input': 'assets/ccimage/object_pdf.html',
        'base_url': 'https://bukoda.gov.ua/npas/pro-nadannia-zghody-na-podil-zemelnoi-dilianky-derzhavnoi-vlasnosti-chernivetskomu-fakhovomu-koledzhu-tekhnolohii-ta-dyzainu',
        'expected': 3,
        'ccimg_html': """<html lang="ua"><body><div class="wrapper"><footer class="footer" id="layout-footer"><div class="footer_top row justify-content-md-between"><div class="col-md-6 col-lg-5"><div class="item first"><ccimage by="img" html=\'&lt;img src="/storage/app/sites/23/logo.svg" alt="" class="footer_logo lowvision_image_filter"&gt;\n\n                    \' format="url">https://bukoda.gov.ua/storage/app/sites/23/logo.svg</ccimage></div></div></div></footer></div></body></html>"""
    },
    {
        'input': 'assets/ccimage/figure_airtical.html',
        'base_url': 'https://www.d-pt.pl/kadry/k/r/1/e1/e2/5c3e22422788a_o.jpg?1579181095',
        'expected': 4,
        'ccimg_html': """<html lang="pl-PL" prefix="og: https://ogp.me/ns#"><body class="product-template-default single single-product postid-2386 theme-starter woocommerce woocommerce-page woocommerce-no-js tinvwl-theme-style"><header class="Header bg-white py-8 lg:py-0 sticky lg:fixed lg:w-full left-0 top-0 transition-all duration-300 z-50"><div class="Container flex justify-between items-center"><div class="Header__logo"><a href="http://15.demooo.pl"><ccimage by="img" html=\'&lt;img src="http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg" alt="Janser Logo"&gt;\' format="url" alt="Janser Logo">http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg</ccimage></a></div></div></header></body></html>"""
    },
    {
        'input': 'assets/ccimage/svg_e.html',
        'base_url': 'https://onlinelibrary.wiley.com/doi/10.1155/2012/387626',
        'expected': 49,
    },
    {
        'input': 'assets/ccimage/inline_image.html',
        'base_url': 'https://community.wikia.com/wiki/Help:Theme_designer',
        'expected': 104,
        'description': '测试标题中的图片被正确处理',
    },
    {
        'input': 'assets/ccimage/svg_ee.html',
        'base_url': 'https://www.spreaker.com/podcast/99-challenges--4769835',
        'expected': 341,
    },
]

TEST_CC_CASE = [
    {
        'url': 'xxx',
        'parsed_content': """<ccimage by="img" html='&lt;img src="http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg" alt="Janser Logo"&gt;' format="url" alt="Janser Logo">http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg</ccimage>""",
        'html': '...',
        'expected': {'type': 'image', 'bbox': [], 'content': {
            'url': 'http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg', 'data': None,
            'alt': 'Janser Logo', 'title': None, 'caption': [], 'footnote': []}},
        'alt': 'Janser Logo',
        'img_url': 'http://15.demooo.pl/wp-content/themes/starter/dist/images/logos/janser-logo.svg'
    },
    {
        'url': 'xxx',
        'parsed_content': """<ccimage by="figure" html='&lt;figure&gt;&lt;img src="http://15.demooo.pl/wp-content/uploads/2022/08/ukladanie-wykladzin.svg" alt="Układanie wykładzin"&gt;&lt;/figure&gt;

                                    ' format="url" alt="Układanie wykładzin">http://15.demooo.pl/wp-content/uploads/2022/08/ukladanie-wykladzin.svg</ccimage>""",
        'html': '...',
        'expected': {'type': 'image', 'bbox': [],
                     'content': {'url': 'http://15.demooo.pl/wp-content/uploads/2022/08/ukladanie-wykladzin.svg',
                                 'data': None, 'alt': 'Układanie wykładzin', 'title': None, 'caption': [], 'footnote': []}},
        'alt': 'Układanie wykładzin',
        'img_url': 'http://15.demooo.pl/wp-content/uploads/2022/08/ukladanie-wykladzin.svg'
    },
    {
        'url': 'xxx',
        'parsed_content': """<img by="figure" html='&lt;figure&gt;&lt;img src="http://15.demooo.pl/wp-content/uploads/2022/08/ukladanie-wykladzin.svg" alt="Układanie wykładzin"&gt;&lt;/figure&gt;

                            ' format="url" alt="Układanie wykładzin">""",
        'html': '...',
        'expected': 31031400,
    },
]
base_dir = Path(__file__).parent


class TestImageRecognizer(unittest.TestCase):
    def setUp(self):
        self.img_recognizer = ImageRecognizer()

    def test_recognize(self):
        for test_case in TEST_CASES_HTML:
            raw_html_path = base_dir.joinpath(test_case['input'])
            base_url = test_case['base_url']
            raw_html = raw_html_path.read_text(encoding='utf-8')
            parts = self.img_recognizer.recognize(base_url, [(html_to_element(raw_html), html_to_element(raw_html))],
                                                  raw_html)
            self.assertEqual(len(parts), test_case['expected'])
            ccimg_datas = [ccimg[0] for ccimg in parts if CCTag.CC_IMAGE in ccimg[0] and 'by="svg"' not in ccimg[0]]
            if ccimg_datas:
                ccimg_data = ccimg_datas[0].replace('\n', '').replace(' ', '')
                ccimg_html = test_case.get('ccimg_html').replace('\n', '').replace(' ', '')
                self.assertEqual(ccimg_data, ccimg_html)

    def test_to_content_list_node(self):
        for test_case in TEST_CC_CASE:
            try:
                res = self.img_recognizer.to_content_list_node(test_case['url'],
                                                               html_to_element(test_case['parsed_content']),
                                                               test_case['html'])
                self.assertEqual(res, test_case['expected'])
                self.assertEqual(res['content']['alt'], test_case['alt'])
                self.assertEqual(res['content']['url'], test_case['img_url'])
            except Exception as e:
                self.assertEqual(e.error_code, test_case['expected'])

    def test_is_under_heading(self):
        """测试识别标题中的图片功能."""
        # 测试一个有标题标签的HTML元素
        html_in_heading = """
        <h1>This is a heading with <img src="test.jpg" alt="Test Image"/> image</h1>
        """
        element = html_to_element(html_in_heading)
        img_element = element.xpath('.//img')[0]

        is_under_heading = self.img_recognizer._ImageRecognizer__is_under_heading(img_element)
        self.assertTrue(is_under_heading, '应该识别出图片在标题标签中')

        # 测试普通图片
        html_normal = """
        <div>This is a normal <img src="test.jpg" alt="Test Image"/> image</div>
        """
        element = html_to_element(html_normal)
        img_element = element.xpath('.//img')[0]

        is_under_heading = self.img_recognizer._ImageRecognizer__is_under_heading(img_element)
        self.assertFalse(is_under_heading, '应该识别出图片不在标题标签中')

    def test_heading_image_removal(self):
        """测试从标题中删除图片的功能."""
        # 创建一个有标题标签的HTML元素
        html_in_heading = """
        <h1>This is a heading with <img src="test.jpg" alt="Test Image"/> image</h1>
        """
        element = html_to_element(html_in_heading)

        base_url = 'http://example.com'
        parts = self.img_recognizer.recognize(base_url, [(element, element)], html_in_heading)

        heading = parts[0][0].xpath('//h1')
        if heading:
            img_in_heading = heading[0].xpath('.//img')
            self.assertEqual(len(img_in_heading), 0, '标题中应该没有img标签')

        if heading:
            heading_text = heading[0].text_content().strip()
            self.assertTrue('This is a heading with' in heading_text, '标题文本应该保留')
            self.assertTrue('image' in heading_text, '标题文本应该保留')

    def test_parse_img_elements_with_various_tags(self):
        """测试解析不同类型的图像标签."""
        # 测试SVG图像
        svg_html = """
        <svg width="100" height="100">
            <circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red"/>
        </svg>
        """
        element = html_to_element(svg_html)
        base_url = 'http://example.com'
        parts = self.img_recognizer.recognize(base_url, [(element, element)], svg_html)
        self.assertTrue(len(parts) > 0, '应该识别SVG图像')

        # 测试picture标签
        picture_html = """
        <picture>
            <source media="(min-width: 800px)" srcset="large.jpg">
            <source media="(min-width: 450px)" srcset="medium.jpg">
            <img src="small.jpg" alt="Test Image">
        </picture>
        """
        element = html_to_element(picture_html)
        parts = self.img_recognizer.recognize(base_url, [(element, element)], picture_html)
        self.assertTrue(len(parts) > 0, '应该识别picture标签中的图像')

        # 测试带有图像URL的iframe标签
        iframe_html = """
        <iframe src="https://example.com/embed/image.jpg"></iframe>
        """
        element = html_to_element(iframe_html)
        self.img_recognizer._ImageRecognizer__parse_img_attr(base_url, element, {})

    def test_parse_svg_img_attr(self):
        """测试SVG图像处理."""
        svg_html = """
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red"/>
        </svg>
        """
        element = html_to_element(svg_html)
        attributes = {'html': svg_html}

        # 调用私有方法处理SVG
        self.img_recognizer._ImageRecognizer__parse_svg_img_attr(element, attributes)

        # 验证结果
        self.assertEqual(attributes['format'], 'base64', 'SVG应该被转换为base64格式')
        self.assertTrue(attributes['text'].startswith('data:image/png;base64,'), 'SVG应该被转换为base64格式的PNG')

    def test_get_full_image_url(self):
        """测试获取完整图像URL的方法."""
        base_url = 'https://example.com/page/index.html'

        # 测试相对路径
        relative_src = 'images/test.jpg'
        full_url = self.img_recognizer._ImageRecognizer__get_full_image_url(base_url, relative_src)
        self.assertEqual(full_url, 'https://example.com/page/images/test.jpg')

        # 测试根路径
        root_src = '/images/test.jpg'
        full_url = self.img_recognizer._ImageRecognizer__get_full_image_url(base_url, root_src)
        self.assertEqual(full_url, 'https://example.com/images/test.jpg')

        # 测试绝对路径
        absolute_src = 'https://another.com/images/test.jpg'
        full_url = self.img_recognizer._ImageRecognizer__get_full_image_url(base_url, absolute_src)
        self.assertEqual(full_url, 'https://another.com/images/test.jpg')

        # 测试协议相对路径
        protocol_src = '//cdn.example.com/images/test.jpg'
        full_url = self.img_recognizer._ImageRecognizer__get_full_image_url(base_url, protocol_src)
        self.assertEqual(full_url, 'https://cdn.example.com/images/test.jpg')

    def test_parse_text_tail(self):
        """测试解析图像文本和尾部文本的方法."""
        attributes = {
            'text': 'https://example.com/image.jpg',
            'tail': '这是尾部文本',
            'format': 'url'
        }

        text, tail = self.img_recognizer._ImageRecognizer__parse_text_tail(attributes)

        self.assertEqual(text, 'https://example.com/image.jpg')
        self.assertEqual(tail, '这是尾部文本')

        # 验证attributes中已移除text和tail
        self.assertNotIn('text', attributes)
        self.assertNotIn('tail', attributes)

    def test_parse_img_text_with_background_image(self):
        """测试解析带有背景图像的样式属性."""
        # 创建一个带有背景图像的样式属性
        elem_attributes = {
            'style': 'background-image: url("https://example.com/bg.jpg"); color: red;'
        }

        text = self.img_recognizer._ImageRecognizer__parse_img_text(elem_attributes)
        self.assertEqual(text, 'https://example.com/bg.jpg')

        # 测试带有src属性的情况
        elem_attributes = {
            'src': 'https://example.com/image.jpg',
            'data-src': 'https://example.com/hires.jpg'
        }

        text = self.img_recognizer._ImageRecognizer__parse_img_text(elem_attributes)
        self.assertEqual(text, 'https://example.com/image.jpg')

        # 测试带有非图像src的情况
        elem_attributes = {
            'src': 'javascript:void(0)',
            'data-img': 'https://example.com/image.jpg'
        }

        text = self.img_recognizer._ImageRecognizer__parse_img_text(elem_attributes)
        self.assertEqual(text, 'https://example.com/image.jpg')

    def test_complex_heading_image_removal(self):
        """测试更复杂的标题中图像删除场景."""
        # 创建一个有多层嵌套和多个图像的标题
        complex_html = """
        <div>
            <h1>This is a <span>heading <img src="first.jpg" alt="First Image"/></span> with
            <a href="#"><img src="second.jpg" alt="Second Image"/></a> multiple images</h1>
            <p>This is a paragraph with <img src="third.jpg" alt="Third Image"/> image</p>
        </div>
        """
        element = html_to_element(complex_html)
        base_url = 'http://example.com'

        # 处理HTML
        parts = self.img_recognizer.recognize(base_url, [(element, element)], complex_html)

        h1_elements = parts[0][0].xpath('//h1')
        if h1_elements:
            img_in_h1 = h1_elements[0].xpath('.//img')
            self.assertEqual(len(img_in_h1), 0, '标题中不应该有img标签')

        # 验证标题文本仍然存在
        if h1_elements:
            heading_text = h1_elements[0].text_content().strip()
            self.assertTrue('This is a heading' in heading_text, '标题文本应该保留')
            self.assertTrue('multiple images' in heading_text, '标题文本应该保留')

        # 检查所有部分，是否包含ccimage标签
        ccimage_found = False
        for part in parts:
            html = element_to_html(part[0])
            if CCTag.CC_IMAGE in html:
                ccimage_found = True
                break

        self.assertTrue(ccimage_found, '应该至少找到一个ccimage标签')

        # 验证原始HTML中的段落图片不再存在为img标签
        p_elements = []
        for part in parts:
            p_elements.extend(part[0].xpath('//p'))

        img_in_p = []
        for p in p_elements:
            img_in_p.extend(p.xpath('.//img'))

        self.assertEqual(len(img_in_p), 0, '段落中不应该有img标签')

    def test_image_caption(self):
        complex_html = """
        <figure class="wp-block-image size-full" data-anno-uid="anno-uid-q4azamuwlp"><img alt=""
                                                                                          cc-select="true"
                                                                                          class="wp-image-163239 mark-selected"
                                                                                          data-anno-uid="anno-uid-trx696xmwg"
                                                                                          decoding="async"
                                                                                          height="899"
                                                                                          loading="lazy"
                                                                                          sizes="(max-width: 900px) 100vw, 730px"
                                                                                          src="https://www.ask.com/wp-content/uploads/sites/3/2022/09/87f86f75062a6a7084c4d95d06e502ea.png"
                                                                                          srcset="https://www.ask.com/wp-content/uploads/sites/3/2022/09/87f86f75062a6a7084c4d95d06e502ea.png?resize=900,505 900w, https://www.ask.com/wp-content/uploads/sites/3/2022/09/87f86f75062a6a7084c4d95d06e502ea.png?resize=730,410 730w, https://www.ask.com/wp-content/uploads/sites/3/2022/09/87f86f75062a6a7084c4d95d06e502ea.png?resize=500,280 500w, https://www.ask.com/wp-content/uploads/sites/3/2022/09/87f86f75062a6a7084c4d95d06e502ea.png?resize=370,207 370w"
                                                                                          style=""
                                                                                          width="1600">
            <figcaption data-anno-uid="anno-uid-6qfcte0y2eh">
                <marked-text cc-select="true" class="mark-selected"
                             data-anno-uid="anno-uid-5ssd5opgc1e">Roger Moore in
                </marked-text>
                <em cc-select="true" class="mark-selected" data-anno-uid="anno-uid-lp7dtyaq7gl"> For
                    Your Eyes Only</em>
                <marked-tail cc-select="true" class="mark-selected"
                             data-anno-uid="anno-uid-1qugevcscpa" style="">. Photo Courtesy: United
                    Artists/Everett Collection
                </marked-tail>
            </figcaption>
        </figure>
        """
        element = html_to_element(complex_html)
        base_url = 'http://example.com'
        parts = self.img_recognizer.recognize(base_url, [(element, element)], complex_html)
        html = element_to_html(parts[0][0])
        self.assertIn('caption="Roger Moore in For Your Eyes Only . Photo Courtesy: United Artists/Everett Collection', html)
