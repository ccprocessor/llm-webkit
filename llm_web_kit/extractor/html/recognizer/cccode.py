from typing import List, Tuple
from urllib.parse import urlparse

from lxml.html import HtmlElement
from overrides import override

from llm_web_kit.extractor.html.recognizer.code import (classes, rules,
                                                        tag_code, tag_pre,
                                                        tag_pre_code)
from llm_web_kit.extractor.html.recognizer.recognizer import (
    BaseHTMLElementRecognizer, CCTag)


class CodeRecognizer(BaseHTMLElementRecognizer):
    @staticmethod
    def remove_empty_code(r: HtmlElement):
        for x in r:  # type: ignore
            if x.tag == CCTag.CC_CODE or x.tag == CCTag.CC_CODE_INLINE:
                if not x.text:
                    r.remove(x)
            else:
                CodeRecognizer.remove_empty_code(x)

    """解析代码元素."""
    @override
    def recognize(
        self,
        base_url: str,
        main_html_lst: List[Tuple[HtmlElement, HtmlElement]],
        raw_html: str,
        language:str = 'en'
    ) -> List[Tuple[HtmlElement, HtmlElement]]:
        """父类，解析代码元素.

        Args:
            base_url: str: 基础url
            main_html_lst: main_html在一层一层的识别过程中，被逐步分解成不同的元素
            raw_html: 原始完整的html

        Returns:
        """
        domain = urlparse(base_url).hostname

        rtn: List[Tuple[HtmlElement, HtmlElement]] = []
        for root, root_raw_html in main_html_lst:
            if self.is_cc_html(root):
                rtn.append((root, root_raw_html))
                continue

            while True:
                # 命中规则，直接处理并跳出
                if rules.detect(domain):
                    rules.modify_tree(domain, root)
                    break

                take_code = False
                # 最常见:
                # <pre><code></code></pre>
                # <code><pre></pre></code>
                # 使用 pre 来保证 code 内部格式
                # 所以每一个 code 就是一段代码，只需要切分出code，合并text
                if tag_pre_code.detect(root):
                    tag_pre_code.modify_tree(root)
                    take_code = True

                # 次常见:
                # 只有 code 没有 pre
                # 网站使用一些 div\span\p\br 来自己控制格式，每个 code 块只有一个单词或者符号。
                # 对 code tag 之间做距离排序，做不完整的最小生成树，挑选出完整的代码块的根节点，再合并内部的 text
                if tag_code.detect(root):
                    tag_code.modify_tree(root)
                    take_code = True

                # 只有 pre 没有 code
                if tag_pre.detect(root):
                    tag_pre.modify_tree(root)
                    take_code = True

                # 如果这个网站没有一种情况 match 到了，那就看看 class 里面又没有带 code 的
                if not take_code and classes.detect(root):
                    classes.modify_tree(root)

                break

            CodeRecognizer.remove_empty_code(root)
            rtn.extend(BaseHTMLElementRecognizer.html_split_by_tags(root, CCTag.CC_CODE))
        return rtn

    @override
    def to_content_list_node(self, base_url:str, parsed_content: HtmlElement, raw_html_segment:str) -> dict:
        """把代码元素转换为content list node. 注意：此方法只处理块级代码(CC_CODE)，行内代码(CC_CODE_INLIN
        E)由TextParagraphRecognizer处理.

        Args:
            base_url:
            parsed_content: HtmlElement对象
            raw_html_segment:

        Returns:
        """
        d = {
            'type': 'code',
            'bbox': [],
            'content': {
                'code_content': parsed_content.text,
            },
        }

        # 可选字段：language
        if lang := parsed_content.get('language', None):
            d['content']['language'] = lang

        # 可选字段：by（代码高亮工具）
        if by := parsed_content.get('by', None):
            d['content']['by'] = by

        return d
