from typing import List, Tuple

from lxml.html import HtmlElement
from overrides import override

from llm_web_kit.exception.exception import (
    HtmlMathMathjaxRenderRecognizerException, HtmlMathRecognizerException)
from llm_web_kit.extractor.html.recognizer.cc_math import (tag_img, tag_math,
                                                           tag_mjx, tag_script)
from llm_web_kit.extractor.html.recognizer.cc_math.common import (CCMATH, CSDN,
                                                                  ZHIHU)
from llm_web_kit.extractor.html.recognizer.cc_math.render.render import (
    BaseMathRender, MathRenderType)
from llm_web_kit.extractor.html.recognizer.recognizer import (
    BaseHTMLElementRecognizer, CCTag)
from llm_web_kit.libs.doc_element_type import DocElementType
from llm_web_kit.libs.html_utils import iter_node


class MathRecognizer(BaseHTMLElementRecognizer):
    """解析数学公式元素."""

    def __init__(self):
        super().__init__()
        self.cm = CCMATH()
        self.mathjax_detected = False  # 添加检测标记

    @override
    def recognize(self, base_url: str, main_html_lst: List[Tuple[HtmlElement, HtmlElement]], raw_html: str, language:str = 'en') -> List[Tuple[HtmlElement, HtmlElement]]:
        """父类，解析数学公式元素.

        Args:
            base_url: str: 基础url
            main_html_lst: main_html在一层一层的识别过程中，被逐步分解成不同的元素，[(cc_html, o_hmtl), (cc_html, o_html)]
            raw_html: 原始完整的html

        Returns: main_html_lst中发现有公式，则返回处理后的元素，标签更新为ccmath，否则原样返回.
        """
        result = []
        self.cm.url = base_url
        # 获取数学公式渲染器
        base_render = BaseMathRender()
        math_render = base_render.get_math_render(raw_html)
        # TODO: 自定义配置目前只支持mathjax
        if math_render and math_render.render_type == MathRenderType.MATHJAX:
            math_render.get_options(raw_html)
        for cc_html, o_html in main_html_lst:
            if not self.is_cc_html(cc_html):
                result.extend(self.process_ccmath_html(cc_html, o_html, math_render, base_url))
            else:
                result.append((cc_html, o_html))
        return result

    @override
    def to_content_list_node(self, base_url: str, parsed_content: HtmlElement, raw_html_segment: str) -> dict:
        """将content转换成content_list_node.
        每种类型的html元素都有自己的content-list格式：参考 docs/specification/output_format/content_list_spec.md
        例如代码的返回格式：
        ```json
            {
                "type": "equation-inline", # 数学公式类型，一共equation-inline和equation-interline两种
                "raw_content": "<ccmath type="latex" by="mathjax">$u_{x_0}^{in}(x)$</ccmath>",
                "content": {
                    "math_content": "u_{x_0}^{in}(x)",
                    "math_type": "latex",
                    "by": "mathjax"
                }
            }
            ```

            Args:
                content: str: 要转换的content

        Returns:
            dict: content_list_node
        """
        tree = parsed_content
        if tree is None:
            raise HtmlMathRecognizerException(f'Failed to load html: {parsed_content}')

        inter_ele = tree.xpath(f'//{CCTag.CC_MATH_INTERLINE}')
        in_els = tree.xpath(f'//{CCTag.CC_MATH_INLINE}')
        if len(inter_ele) > 0:
            # 获取math_content
            math_content = inter_ele[0].text
            math_content = self.cm.wrap_math_md(math_content)
            return {
                'type': DocElementType.EQUATION_INTERLINE,
                'raw_content': raw_html_segment,
                'content': {
                    'math_content': math_content,
                    'math_type': inter_ele[0].get('type'),  # 数学语言类型
                    'by': inter_ele[0].get('by')  # 数学语言渲染器
                }
            }
        elif len(in_els) > 0:
            math_content = in_els[0].text
            return {
                'type': DocElementType.EQUATION_INLINE,
                'raw_content': raw_html_segment,
                'content': {
                    'math_content': math_content,
                    'math_type': in_els[0].get('type'),  # 数学语言类型
                    'by': in_els[0].get('by')  # 数学语言渲染器
                }
            }
        else:
            raise HtmlMathRecognizerException(f'No ccmath element found in content: {parsed_content}')

    def process_ccmath_html(self, cc_html: str, o_html: str, math_render: BaseMathRender, base_url: str) -> List[Tuple[str, str]]:
        """处理数学公式，将外层标签修改为 ccmath.

        Args:
            cc_html: 处理后的HTML
            o_html: 原始HTML

        Returns:
            List[Tuple[str, str]]: 处理后的HTML对
        """
        # node是从cc_html中解析出来的lxml节点
        try:
            self.cm.url = base_url
            tree = cc_html
            math_render_type = math_render.get_render_type()

            # process1: node循环逻辑
            for node in iter_node(tree):
                assert isinstance(node, HtmlElement)
                original_html = self._element_to_html(node)
                parent = node.getparent()

                # 针对csdn博客中的katex标签，提取latex公式
                if (CSDN.DOMAIN in self.cm.url and
                        node.tag == 'span' and
                        node.get('class') in [CSDN.INLINE, CSDN.DISPLAY]):
                    tag_script.process_katex_mathml(self.cm, math_render_type, node)

                if ZHIHU.DOMAIN in self.cm.url and node.tag == 'span' and node.get('class') == ZHIHU.MATH:
                    tag_script.process_zhihu_custom_tag(self.cm, math_render_type, node)

                # 提示：被mathjax兜底覆盖，逻辑已经删除
                # tag = span， class 为 math-containerm， 或者 mathjax 或者 wp-katex-eq
                # if node.tag == 'span' and node.get('class') and (
                #         'math-container' in node.get('class') or
                #         'mathjax' in node.get('class') or
                #         'wp-katex-eq' in node.get('class') or
                #         'x-ck12-mathEditor' in node.get('class') or
                #         'tex' in node.get('class')
                # ):
                #     tag_common_modify.modify_tree(self.cm, math_render_type, original_html, node, parent)

                # math tags
                if node.tag == 'math' or node.tag.endswith(':math'):
                    # print(f"匹配到数学标签: {node.tag}")
                    # print(f"标签内容: {original_html}")
                    tag_math.modify_tree(self.cm, math_render_type, original_html, node, parent)

                if node.tag == 'mjx-container':
                    tag_mjx.modify_tree(self.cm, math_render, original_html, node)

                # img中的latex
                if node.tag == 'img':
                    tag_img.modify_tree(self.cm, math_render_type, original_html, node, parent)

                # span.katex
                if node.tag == 'script' or 'math' == node.get('class') or 'katex' == node.get('class'):
                    # print('匹配到script/math/katex标签: ', original_html)
                    tag_script.modify_tree(self.cm, math_render_type, original_html, node, parent)

            # procsee2: mathjax渲染器逻辑
            try:
                # case1：有mathjax配置
                if math_render_type == MathRenderType.MATHJAX:
                    math_render.find_math(tree)
                # case2：其他情况默认开启 Mathjax配置
                else:
                    from llm_web_kit.extractor.html.recognizer.cc_math.render.mathjax import \
                        MathJaxRenderMock
                    math_render = MathJaxRenderMock()
                    math_render.find_math(tree)
            except Exception as e:
                raise HtmlMathMathjaxRenderRecognizerException(f'处理MathjaxRender数学公式失败: {e}')
            # 保存处理后的html
            # with open('test20250702_result.html', 'w', encoding='utf-8') as f:
            #     f.write(self._element_to_html(tree))
        except Exception as e:
            raise HtmlMathRecognizerException(f'处理数学公式失败: {e}')
        return self.html_split_by_tags(tree, [CCTag.CC_MATH_INTERLINE])


if __name__ == '__main__':
    math_recognizer = MathRecognizer()
    # test_html = [
    #     (
    #         ("""
    #     <div>
    #         <script type="math/tex">x^2 + y^2 = z^2</script>
    #         <script type="math/tex"></script>
    #         <script type="math/tex; mode=display">E=mc^2</script>
    #     </div>
    #     """),
    #         ("""
    #     <div>
    #         <script type="math/tex">x^2 + y^2 = z^2</script>
    #         <script type="math/tex"></script>
    #         <script type="math/tex; mode=display">E=mc^2</script>
    #     </div>
    #     """)
    #     )
    # ]
    # raw_html = (
    #     '<head> '
    #     '<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js'
    #     '?config=TeX-MML-AM_CHTML"> </script> '
    #     '</head> '
    #     '<p>这是p的text<span class="mathjax_display">$$a^2 + b^2 = c^2$$</span>这是span的tail<b>这是b的text</b>这是b的tail</p>'
    # )
    # ——————————————测试代码——————————————————
    # ↓ 要测试的html文件 ↓
    # with open(r'C:\Users\10412\.ssh\llm-webkit-mirror\tests\llm_web_kit\extractor\html\recognizer\assets\ccmath\asciimath.html', 'r', encoding='utf-8') as f:
    #     raw_html = f.read()
    # from llm_web_kit.libs.html_utils import html_to_element
    # root = html_to_element(raw_html)
    # math_recognizer.recognize(
    #         'https://www.baidu.com',
    #         [(root, root)],
    #         raw_html
    #     )
    # ———————————————————————————————————————
    # raw_html = open('bench/data/origin/math_physicsforums_1.html', 'r').read()
    # print(math_recognizer.recognize(
    #     'https://www.baidu.com',
    #     [(raw_html, raw_html)],
    #     raw_html
    # ))
    # print(math_recognizer.to_content_list_node(
    #     'https://www.baidu.com',
    #     '<ccmath-interline type="latex" by="mathjax">$u_{x_0}^{in}(x)$</ccmath-interline>',
    #     # raw_html,
    #     raw_html
    # ))
    # print(math_recognizer.html_split_by_tags(
    #     raw_html,
    #     ['ccmath']
    # ))
    # raw_html = open('bench/data/origin/math_physicsforums_1.html', 'r').read()
    # print(math_recognizer.recognize(
    #     'https://www.baidu.com',
    #     [(raw_html, raw_html)],
    #     raw_html
    # ))
