import base64
import re
from typing import List, Tuple
from urllib.parse import urljoin, urlparse

import cairosvg
from lxml.html import HtmlElement
from overrides import override

from llm_web_kit.exception.exception import HtmlImageRecognizerException
from llm_web_kit.extractor.html.recognizer.recognizer import (
    BaseHTMLElementRecognizer, CCTag)
from llm_web_kit.libs.doc_element_type import DocElementType
from llm_web_kit.libs.html_utils import remove_element


class ImageRecognizer(BaseHTMLElementRecognizer):
    """解析图片元素."""
    IMG_LABEL = ['.jpg', '.jpeg', '.png', '.gft', '.webp', '.bmp', '.svg', 'data:image', '.gif']  # '.pdf'

    @override
    def to_content_list_node(self, base_url: str, parsed_content: HtmlElement, raw_html_segment: str) -> dict:
        """将content转换成content_list_node.
        每种类型的html元素都有自己的content-list格式：参考 docs/specification/output_format/content_list_spec.md
        例如代码的返回格式：
        ```json
        {
            "type": "code",
            "bbox": [0, 0, 50, 50],
            "raw_content": "<code>def add(a, b):\n    return a + b</code>" // 原始的html代码
            "content": {
                  "code_content": "def add(a, b):\n    return a + b",
                  "language": "python",
                  "by": "hilightjs"
            }
        }
        ```

        Args:
            base_url: str: 基础url
            parsed_content: str: 被解析后的内容<ccmath ...>...</ccmath>等
            raw_html_segment: str: 原始html片段

        Returns:
            dict: content_list_node
        """
        # html_obj = self._build_html_tree(parsed_content)
        html_obj = parsed_content

        if html_obj.tag == CCTag.CC_IMAGE:
            return self.__ccimg_to_content_list(raw_html_segment, html_obj)
        else:
            raise HtmlImageRecognizerException(f'No ccimage element found in content: {parsed_content}')

    def __ccimg_to_content_list(self, raw_html_segment: str, html_obj: HtmlElement) -> dict:
        caption = html_obj.get('caption')
        footnote = html_obj.get('footnote')
        result = {
            'type': DocElementType.IMAGE,
            'bbox': [],
            'content': {
                'url': html_obj.text if html_obj.get('format') == 'url' else None,
                'data': html_obj.text if html_obj.get('format') == 'base64' else None,
                'alt': html_obj.get('alt'),
                'title': html_obj.get('title'),
                'caption': [caption] if caption else [],
                'footnote': [footnote] if footnote else []
            }
        }
        return result

    @override
    def recognize(self, base_url: str, main_html_lst: List[Tuple[HtmlElement, HtmlElement]], raw_html: str, language:str = 'en') -> List[
        Tuple[HtmlElement, HtmlElement]]:
        """父类，解析图片元素.

        Args:
            base_url: str: 基础url
            main_html_lst: main_html在一层一层的识别过程中，被逐步分解成不同的元素
            raw_html: 原始完整的html

        Returns:
        """
        ccimg_html = list()
        for html_li in main_html_lst:
            if self.is_cc_html(html_li[0]):
                ccimg_html.append(html_li)
            else:
                new_html_li = self.__parse_html_img(base_url, html_li)
                if new_html_li:
                    ccimg_html.extend(new_html_li)
                else:
                    ccimg_html.append(html_li)
        return ccimg_html

    def __parse_html_img(self, base_url: str, html_str: Tuple[HtmlElement, HtmlElement]) -> List[
        Tuple[HtmlElement, HtmlElement]]:
        """解析html，获取img标签."""
        # html_obj = self._build_html_tree(html_str[0])
        html_obj = html_str[0]
        image_related_selectors = [
            '//*[contains(@class, "image-embed") or contains(@id, "image-embed")]',  # 可能包含嵌入图片的自定义标签
            '//*[starts-with(@src, "data:image/") and not(self::img)]',
            # 带有内嵌base64图片的标签,data:image/png;base64,eg:img, svg/image
            '//iframe[not(ancestor::noscript) and not(ancestor::iframe) and not(ancestor::object)]',
            '//embed[not(ancestor::object)]',
            '//figure[not(ancestor::figure)]',
            '//object[not(ancestor::object)]',  # object标签，通常用于嵌入多媒体内容
            '//picture[not(ancestor::figure) and not(ancestor::object)]',
            '//canvas',  # canvas标签，可能用于绘制图形或展示图片
            '//svg[not(ancestor::figure)]',  # svg标签，用于矢量图形
            '//video',
            '//audio',
            '//article',
            '//img[not(ancestor::noscript) and not(ancestor::picture) and not(ancestor::figure) and not(ancestor::object) and not(ancestor::table)]',
        ]
        # 合并XPath表达式
        combined_xpath = '|'.join(image_related_selectors)
        # 使用XPath选择所有相关标签
        img_elements = html_obj.xpath(combined_xpath)
        base_img = html_obj.xpath('//*[starts-with(@xlink:href, "data:image/") and not(self::img)]', namespaces={
            'xlink': 'http://www.w3.org/1999/xlink'})
        if base_img:
            img_elements.extend(base_img)
        if img_elements:
            update_html, img_tag = self.__parse_img_elements(base_url, img_elements, html_obj)
            if img_tag:
                return self.html_split_by_tags(update_html, CCTag.CC_IMAGE)

    def __is_under_heading(self, elem: HtmlElement) -> bool:
        """检查元素是否在标题(h1-h6)标签下."""
        # 使用while循环一直往上找parent
        current = elem
        heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        # 检查元素自身的属性，是否已经被标记为内联图像
        if elem.get('inline') == 'true':
            return True

        while current is not None:
            parent = current.getparent()
            if parent is None:
                return False
            if parent.tag in heading_tags:
                return True

            current = parent

        return False

    def __parse_img_elements(self, base_url: str, img_elements: HtmlElement, html_obj: HtmlElement) -> HtmlElement:
        """解析img标签."""
        img_tag = []
        is_valid_img = False
        for elem in img_elements:
            tag = elem.tag
            raw_img_html = self._element_to_html(elem)
            attributes = {
                'by': tag,
                'html': raw_img_html,  # 保留原始 <img> 标签作为属性值
                'format': 'url',  # 指定图片格式，url|base
            }
            attributes['caption'] = elem.xpath('normalize-space()')
            if tag in ['embed', 'object', 'iframe', 'video', 'audio', 'canvas']:
                if not [img_elem for img_elem in self.IMG_LABEL if
                        img_elem in raw_img_html.lower()]:
                    continue
                elif elem.xpath('.//img|.//image'):
                    if len(elem.xpath('.//img|.//image')) == 1:
                        self.__parse_img_attr(base_url, elem.xpath('.//img|.//image')[0], attributes)
                    else:
                        continue
                else:
                    self.__parse_img_attr(base_url, elem, attributes)
            elif tag in ['picture', 'figure']:
                if elem.xpath('.//img|.//image'):
                    self.__parse_img_attr(base_url, elem.xpath('.//img|.//image')[0], attributes)
                else:
                    continue
            elif tag == 'svg':
                if elem.xpath('.//path|.//circle'):
                    self.__parse_svg_img_attr(elem, attributes)
                elif elem.xpath('.//img|.//image'):
                    self.__parse_img_attr(base_url, elem.xpath('.//img|.//image')[0], attributes)
                else:
                    continue
            elif tag == 'article':
                if elem.xpath('.//header'):
                    self.__parse_img_attr(base_url, elem.xpath('.//header')[0], attributes)
                else:
                    continue
            else:
                self.__parse_img_attr(base_url, elem, attributes)
            if not attributes.get('text'):
                continue

            is_valid_img = True

            # 处理标题中的图像
            is_under_heading = self.__is_under_heading(elem)
            if is_under_heading:
                # 保留标题的原始结构，只移除图像
                img_tag.append(CCTag.CC_IMAGE)
                remove_element(elem)
            else:
                img_tag.append(CCTag.CC_IMAGE)
                img_text, img_tail = self.__parse_text_tail(attributes)
                new_ccimage = self._build_cc_element(CCTag.CC_IMAGE, img_text, img_tail, **attributes)
                self._replace_element(elem, new_ccimage)

        if is_valid_img:
            # updated_html = self._element_to_html(html_obj)
            updated_html = html_obj
            return (updated_html, img_tag)
        else:
            return (None, None)

    def __parse_img_attr(self, base_url: str, elem: HtmlElement, attributes: dict):
        """解析获取img标签属性值."""
        elem_attributes = {k: v for k, v in elem.attrib.items() if v and v.strip()}
        text = self.__parse_img_text(elem_attributes)
        if text:
            if text.startswith('data:image'):
                attributes['text'] = text
                attributes['format'] = 'base64'
            else:
                attributes['text'] = self.__get_full_image_url(base_url, text)
        common_attributes = ['alt', 'title', 'width', 'height', 'style']  # , 'src', 'style', 'data-src', 'srcset'
        attributes.update({attr: elem_attributes.get(attr) for attr in common_attributes if elem_attributes.get(attr)})
        if elem.tail and elem.tail.strip():
            attributes['tail'] = elem.tail.strip()

    def __parse_img_text(self, elem_attributes: dict):
        text = ''
        # 获取并清理 style 属性值
        style = elem_attributes.get('style', '').replace('\\"', '"').strip()

        # 处理 background-image URL
        if 'background-image' in style:
            try:
                url_part = style.partition('background-image:')[2]  # 获取 url(...) 部分
                bg_url = url_part.partition('url(')[2].split(')')[0].strip(" '\"")
                if any(img_label for img_label in self.IMG_LABEL if img_label in bg_url.lower()):
                    return bg_url
            except HtmlImageRecognizerException:
                pass

        # 原有的 src 处理逻辑
        src = elem_attributes.get('src')
        data_src = [v.split(' ')[0] for k, v in elem_attributes.items() if k.startswith('data')]

        if src and data_src:
            src = src if not src.startswith('data:image') else data_src[0]
        if src and any(img_label for img_label in self.IMG_LABEL if img_label in src.lower()):
            text = src
        else:
            for k, v in elem_attributes.items():
                if any(img_label for img_label in self.IMG_LABEL if img_label in v.lower().split('?')[0]):
                    if 'http' in v.strip()[1:-1]:
                        continue
                    text = v
        return text

    def __parse_svg_img_attr(self, elem: HtmlElement, attributes: dict):
        if [k for k, v in elem.attrib.items() if k == 'xmlns']:
            elem.attrib.pop('xmlns')
            svg_img = self.__svg_to_base64(self._element_to_html(elem))
        else:
            svg_img = self.__svg_to_base64(attributes['html'])
        if svg_img:
            attributes['text'] = svg_img
            attributes['format'] = 'base64'
            if elem.tail and elem.tail.strip():
                attributes['tail'] = elem.tail.strip()
            common_attributes = ['alt', 'title', 'width', 'height']
            for attr in common_attributes:
                if elem.get(attr) is not None:
                    attributes[attr] = elem.get(attr)

    def __parse_text_tail(self, attributes: dict) -> Tuple[str, str]:
        """解析img标签的text&tail值."""
        text = attributes.pop('text') if attributes.get('text') else ''
        tail = attributes.pop('tail') if attributes.get('tail') else ''
        return (text, tail)

    def __get_full_image_url(self, base_url: str, relative_src: str) -> str:
        parsed_base = urlparse(base_url)
        base_domain = f'{parsed_base.scheme}://{parsed_base.netloc}'

        if relative_src.startswith('http'):
            return relative_src
        elif relative_src.startswith('/'):
            return urljoin(base_domain, relative_src)
        elif relative_src.startswith('//'):
            return urljoin(parsed_base.scheme, relative_src)
        else:
            return urljoin(base_url, relative_src)

    def __svg_to_base64(self, svg_content: str) -> str:
        try:
            if not svg_content.strip().endswith('svg>'):
                svg_content = re.search(r'(<svg.*svg>)', svg_content, re.DOTALL).group(1)
            image_data = cairosvg.svg2png(bytestring=svg_content)
            base64_data = base64.b64encode(image_data).decode('utf-8')
            mime_type = 'image/png'
            return (
                f'data:{mime_type};'
                f'base64,{base64_data}'
            )
        except ValueError:
            pass
        except Exception as e:
            if 'not well-formed (invalid token)' in str(e):  # 原svg数据异常，这里过滤掉不做处理
                pass
            else:
                HtmlImageRecognizerException(f'parse svg error: {e}, svg data: {svg_content}')
