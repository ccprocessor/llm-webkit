import re
from typing import Any, Dict, List

from pylatexenc import latexwalker

from llm_web_kit.extractor.html.recognizer.cc_math.common import CCMATH
from llm_web_kit.extractor.html.recognizer.cc_math.render.render import (
    BaseMathRender, MathRenderType)
from llm_web_kit.libs.html_utils import (HtmlElement, SimpleMatch,
                                         html_to_element)
from llm_web_kit.libs.text_utils import normalize_ctl_text

# 添加MATHJAX_OPTIONS变量定义
MATHJAX_OPTIONS = {
    'inlineMath': [['$', '$'], ['\\(', '\\)'], ['\\\\(', '\\\\)'], ['[itex]', '[/itex]']],
    'displayMath': [['$$', '$$'], ['\\[', '\\]'], ['\\\\[', '\\\\]'], ['[tex]', '[/tex]']],
    'processEscapes': True,
    'processEnvironments': True,
    'processRefs': True,
    'processascii': False,
    'skipTags': ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
    'ignoreClass': 'tex2jax_ignore',
    'processClass': 'tex2jax_process',
    'elements': ['body'],
}

# ASCIIMath相关脚本关键词，作为开启ASCII反引号分隔符的依据，可继续补充
ASCIIMATH_KEYWORDS = [
    # case1: <script type="text/javascript" src="javascript/ASCIIMathMLeditor.js"></script>
    'ASCIIMath',
    # case2: <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.6/latest.js?config=AM_CHTML"></script>
    'AM_CHTML'
]

# 独立公式环境
independent_math_environments = [
    'displaymath',
    'equation',
    'equation*',
    'align',
    'align*',
    'gather',
    'gather*',
    'multline',
    'multline*',
    'vmatrix',
    'Vmatrix'
]


class MathJaxRender(BaseMathRender):
    """MathJax渲染器实现."""

    def __init__(self):
        """初始化MathJax渲染器."""
        super().__init__()
        self.render_type = MathRenderType.MATHJAX
        self.options = {
            'inlineMath': [],
            'displayMath': [],
            'extensions': [],
            'config': '',
            'version': ''
        }
        self.ccmath = CCMATH()  # 初始化CCMATH实例

    def get_render_type(self) -> str:
        """获取渲染器类型."""
        return self.render_type

    def get_options(self, html: str) -> Dict[str, Any]:
        """从HTML中提取MathJax选项.

        Args:
            html: 包含MathJax配置的HTML字符串

        Returns:
            Dict[str, Any]: MathJax选项字典
        """
        tree = html_to_element(html)
        if tree is None:
            return self.options

        # 查找MathJax配置脚本
        for script in tree.iter('script'):
            if script.get('type') == 'text/x-mathjax-config':
                self._parse_mathjax_config(script.text)

            # 检查MathJax版本和配置
            src = script.get('src', '')
            if 'mathjax' in src.lower():
                self._parse_mathjax_version(src)

                # 检查配置参数
                if '?' in src:
                    config_part = src.split('?', 1)[1]
                    if 'config=' in config_part:
                        config = re.search(r'config=([^&]+)', config_part)
                        if config:
                            self.options['config'] = config.group(1)

        # 检测ASCIIMath脚本并更新选项
        self.options['processascii'] = self._detect_ascii_math(tree)
        return self.options

    def _parse_mathjax_config(self, config_text: str) -> None:
        """解析MathJax配置脚本.

        Args:
            config_text: MathJax配置脚本内容
        """
        if not config_text:
            return

        # 提取行内公式分隔符
        inline_pattern = (
            r'inlineMath:\s*\['
            r'\s*(\[.*?\](?:\s*,\s*\[.*?\])*)\s*\]'
        )
        inline_match = re.search(inline_pattern, config_text, re.DOTALL)
        if inline_match:
            delimiters_str = inline_match.group(1)
            self.options['inlineMath'] = self._parse_delimiters(delimiters_str)

        # 提取行间公式分隔符
        display_pattern = (
            r'displayMath:\s*\['
            r'\s*(\[.*?\](?:\s*,\s*\[.*?\])*)\s*\]'
        )
        display_match = re.search(display_pattern, config_text, re.DOTALL)
        if display_match:
            delimiters_str = display_match.group(1)
            self.options['displayMath'] = self._parse_delimiters(delimiters_str)

        # 提取扩展
        extensions_pattern = (
            r'extensions:\s*\['
            r'\s*([\'"].*?[\'"](?:\s*,\s*[\'"].*?[\'"])*)\s*\]'
        )
        extensions_match = re.search(extensions_pattern, config_text, re.DOTALL)
        if extensions_match:
            extensions_str = extensions_match.group(1)
            self.options['extensions'] = [
                ext.strip('\'"')
                for ext in re.findall(r'[\'"].*?[\'"]', extensions_str)
            ]

    def _parse_mathjax_version(self, src: str) -> None:
        """解析MathJax版本.

        Args:
            src: MathJax脚本的src属性
        """
        version_match = re.search(r'mathjax/(\d+\.\d+\.\d+)', src, re.IGNORECASE)
        if version_match:
            self.options['version'] = version_match.group(1)
        elif 'latest.js' in src:
            self.options['version'] = 'latest'

    def _parse_delimiters(self, delimiters_str: str) -> List[List[str]]:
        """解析分隔符字符串.

        Args:
            delimiters_str: 分隔符字符串，如 "['$', '$'], ['\\\\(', '\\\\)']"

        Returns:
            List[List[str]]: 分隔符列表
        """
        delimiters = []
        # 匹配 ['x', 'y'] 形式的分隔符对
        pattern = r"\[\s*[\"'](.+?)[\"']\s*,\s*[\"'](.+?)[\"']\s*\]"
        for match in re.finditer(pattern, delimiters_str):
            start, end = match.groups()
            # 处理转义字符
            start = start.replace('\\\\', '\\')
            end = end.replace('\\\\', '\\')
            delimiters.append([start, end])
        return delimiters

    def _is_list_contained(self, list1: List[List[str]], list2: List[List[str]]) -> bool:
        """判断list1中的元素是否都被list2包含.

        Args:
            list1: 第一个列表
            list2: 第二个列表

        Returns:
            bool: 如果list1中的所有元素都被list2包含，则返回True，否则返回False
        """
        if not list1:
            return True

        # 将list2转换为集合，方便查找
        list2_set = {tuple(item) for item in list2}

        # 检查list1中的每个元素是否都在list2中
        for item in list1:
            if tuple(item) not in list2_set:
                return False

        return True

    def is_customized_options(self) -> bool:
        """是否与默认配置不同."""
        # 如果options中inlineMath和displayMath为空，则认为没有自定义配置
        if self.options.get('inlineMath') == [] and self.options.get('displayMath') == []:
            return False

        # 检查inlineMath是否被默认配置包含
        if not self._is_list_contained(
            self.options.get('inlineMath', []),
            MATHJAX_OPTIONS['inlineMath']
        ):
            self.render_type = MathRenderType.MATHJAX_CUSTOMIZED
            return True

        # 检查displayMath是否被默认配置包含
        if not self._is_list_contained(
            self.options.get('displayMath', []),
            MATHJAX_OPTIONS['displayMath']
        ):
            self.render_type = MathRenderType.MATHJAX_CUSTOMIZED
            return True

        return False

    def find_math(self, root: HtmlElement) -> None:
        """查找MathJax格式的数学公式，并创建相应的数学公式节点.

        Args:
            root: HTML根节点
        """
        # 获取行内和行间公式分隔符
        inline_delimiters = self.options.get('inlineMath', [])
        if not inline_delimiters:
            # 使用默认分隔符
            inline_delimiters = MATHJAX_OPTIONS.get(
                'inlineMath', [['$', '$'], ['\\(', '\\)']]
            )

        # 如果processascii为True，添加反引号分隔符
        inline_delimiters = self._add_backtick_delimiter(inline_delimiters)

        display_delimiters = self.options.get('displayMath', [])
        if not display_delimiters:
            # 使用默认分隔符
            display_delimiters = MATHJAX_OPTIONS.get(
                'displayMath', [['$$', '$$'], ['\\[', '\\]']]
            )

        # 预编译正则表达式模式以提高性能
        inline_patterns = []
        for start, end in inline_delimiters:
            start_escaped = re.escape(start)
            end_escaped = re.escape(end)
            pattern = f'{start_escaped}(.*?){end_escaped}'
            inline_patterns.append(pattern)

        display_patterns = []
        for start, end in display_delimiters:
            start_escaped = re.escape(start)
            end_escaped = re.escape(end)
            pattern = f'{start_escaped}(.*?){end_escaped}'
            display_patterns.append(pattern)

        # 添加对环境的支持
        # if MATHJAX_OPTIONS.get('processEnvironments', True):
        #     # 通用匹配任何 \begin{...}\end{...} 环境的模式，保证环境名称相同时才匹配
        #     env_pattern = r'(\\begin\{(?P<env>[^}]+)\}.*?\\end\{(?P=env)\})'
        #     display_patterns.append(env_pattern)

        # 编译正则表达式
        inline_pattern = re.compile('|'.join(inline_patterns), re.DOTALL)
        display_pattern = re.compile('|'.join(display_patterns), re.DOTALL)

        # 处理所有文本节点
        self._find_math_in_element(root, inline_pattern, display_pattern)

    def _find_math_in_element(self, element: HtmlElement, inline_pattern: re.Pattern, display_pattern: re.Pattern) -> None:
        """递归处理元素中的数学公式.

        Args:
            element: 当前元素
            inline_pattern: 行内公式正则表达式
            display_pattern: 行间公式正则表达式
        """
        if element is None:
            return

        # 先处理tail，再处理text，text的判断会多一些
        if element.tail:
            # 处理行间公式（优先处理，因为可能包含行内公式）
            element.tail = self._process_math_in_text(element, element.tail, display_pattern, True, True)
            # 处理行内公式
            if element.tail:  # 检查是否还有文本需要处理
                element.tail = self._process_math_in_text(element, element.tail, inline_pattern, False, True)

        # 跳过特定标签
        skip_tags = MATHJAX_OPTIONS['skipTags']
        if element.tag in skip_tags:
            return
        # 跳过ccmath标签
        from llm_web_kit.extractor.html.recognizer.recognizer import \
            BaseHTMLElementRecognizer

        # 新增方法is_cc_tag_node，该方法值判断当前节点是否是cc标签，而不判断子节点
        if BaseHTMLElementRecognizer.is_cc_tag_node(element):
            return

        # 检查是否应该忽略该元素
        if self._should_ignore_element(element):
            return

        # 处理当前节点的文本
        if element.text:
            # 处理行间公式（优先处理，因为可能包含行内公式）
            element.text = self._process_math_in_text(element, element.text, display_pattern, True)
            # 处理行内公式
            if element.text:  # 检查是否还有文本需要处理
                element.text = self._process_math_in_text(element, element.text, inline_pattern, False)

        # 获取子节点的副本，以避免在迭代过程中修改列表
        children = list(element)

        # 递归处理子节点
        for child in children:
            self._find_math_in_element(child, inline_pattern, display_pattern)

    def _should_ignore_element(self, element: HtmlElement) -> bool:
        """检查是否应该忽略该元素.

        Args:
            element: 当前元素

        Returns:
            bool: 如果应该忽略该元素，则返回True，否则返回False
        """
        # 检查是否有忽略类
        ignore_class = MATHJAX_OPTIONS.get('ignoreClass', 'tex2jax_ignore')
        if element.get('class') and ignore_class in element.get('class'):
            return True

        # 检查是否有处理类
        process_class = MATHJAX_OPTIONS.get('processClass', 'tex2jax_process')
        if process_class and element.get('class') and process_class in element.get('class'):
            return False

        # 检查父元素是否应该被忽略
        parent = element.getparent()
        if parent is not None and self._should_ignore_element(parent):
            return True

        return False

    def _process_math_in_text(
        self,
        element: HtmlElement,
        text: str,
        pattern: re.Pattern,
        is_display: bool,
        is_tail: bool = False
    ) -> str:
        """处理文本中的数学公式.

        Args:
            element: 元素
            text: 文本内容
            pattern: 正则表达式模式
            is_display: 是否为行间公式
            is_tail: 是否为尾部文本

        Returns:
            str: 处理后的文本
        """
        if not text:
            return text

        # 首先查找所有分隔符形式的匹配
        if not is_display:
            matches = list(pattern.finditer(text))
        else:
            matches = []
            tem_match_display = []
            walker = latexwalker.LatexWalker(text)
            nodelist, pos, len_ = walker.get_latex_nodes(pos=0)
            for node in nodelist:
                # 标准的数学环境
                if node.isNodeType(latexwalker.LatexMathNode):
                    # 判断是行内公式还是独立公式
                    if node.displaytype == 'inline':
                        pass
                    elif node.displaytype == 'display':
                        tem_match_display.append(node.latex_verbatim())
                        fake_match = SimpleMatch(text, node.pos, node.len)
                        matches.append(fake_match)
                # 其他数学环境
                if (node.isNodeType(latexwalker.LatexEnvironmentNode) and
                        hasattr(node, 'environmentname') and
                        node.environmentname in independent_math_environments):
                    tem_match_display.append(node.latex_verbatim())
                    fake_match = SimpleMatch(text, node.pos, node.len)
                    matches.append(fake_match)
            # 公式自定义边界逻辑
            new_display_patterns = [item for item in pattern.pattern.split('|') if "$" not in item]
            custom_pattern = re.compile('|'.join(new_display_patterns), re.DOTALL)
            custom_matches = list(custom_pattern.finditer(text))
            for item in custom_matches:
                if item.group() not in tem_match_display:
                    matches.append(item)
            tem_match_display.clear()
        # 如果没有匹配到分隔符形式的公式，直接返回原文本
        if not matches:
            return text

        # 从后向前处理，以避免位置偏移
        result = text
        last_position = len(result)
        parent = element.getparent()

        for match in reversed(matches):
            # 确定匹配的分组索引
            group_idx = 0
            for i in range(1, len(match.groups()) + 1):
                if match.group(i) is not None:
                    group_idx = i
                    break

            formula = match.group(group_idx)
            formula = normalize_ctl_text(formula)
            if not formula.strip():
                continue  # 跳过空公式

            # 检查是否是转义的分隔符
            if self._is_escaped_delimiter(text, match.start()):
                continue

            original_match = match.group(0)
            if self._is_ascii_math_formula(original_match):
                formula = self._extract_ascii_math_content(original_match)
            else:
                formula = self.ccmath.wrap_math_md(formula)

            start_pos = match.start()
            end_pos = match.end()

            # 提取公式后的文本
            suffix = result[end_pos:last_position]

            # 创建数学公式节点
            from llm_web_kit.extractor.html.recognizer.cc_math.common import \
                MathType
            from llm_web_kit.extractor.html.recognizer.recognizer import CCTag
            from llm_web_kit.libs.html_utils import build_cc_element

            tag_name = CCTag.CC_MATH_INTERLINE if is_display else CCTag.CC_MATH_INLINE

            # 使用build_cc_element创建节点
            math_node = build_cc_element(
                html_tag_name=tag_name,
                text=formula,
                tail=suffix,  # 设置公式节点的tail为公式后的文本
                type=MathType.LATEX,
                by=self.render_type,
                html=match.group(0)  # 使用完整的原始HTML
            )

            # 更新结果文本，只保留公式前的部分
            result = result[:start_pos]

            # 将节点添加到适当的位置
            if is_tail:
                # 处理element.tail的情况
                element.tail = result
                if parent is not None:
                    parent_index = list(parent).index(element)
                    parent.insert(parent_index + 1, math_node)
            else:
                # 处理element.text的情况
                element.text = result
                if len(element) > 0:
                    element.insert(0, math_node)
                else:
                    element.append(math_node)

            # 更新last_position
            last_position = start_pos

        # 返回处理后的文本
        return result

    def _is_escaped_delimiter(self, text: str, pos: int) -> bool:
        """检查分隔符是否被转义.

        Args:
            text: 文本内容
            pos: 分隔符位置

        Returns:
            bool: 如果分隔符被转义，则返回True，否则返回False
        """
        # 检查是否启用了转义处理
        if not MATHJAX_OPTIONS.get('processEscapes', True):
            return False

        # 检查分隔符前是否有奇数个反斜杠
        count = 0
        i = pos - 1
        while i >= 0 and text[i] == '\\':
            count += 1
            i -= 1

        # 奇数个反斜杠表示转义
        return count % 2 == 1

    def _add_backtick_delimiter(self, inline_delimiters: List[List[str]]) -> List[List[str]]:
        """如果启用了processascii，添加反引号分隔符.

        Args:
            inline_delimiters: 现有的行内分隔符列表

        Returns:
            List[List[str]]: 可能包含反引号分隔符的分隔符列表
        """
        if self.options.get('processascii', False):
            backtick_delimiter = ['`', '`']
            if backtick_delimiter not in inline_delimiters:
                return inline_delimiters + [backtick_delimiter]
        return inline_delimiters

    def _is_ascii_math_formula(self, match_text: str) -> bool:
        """检查是否是ASCII数学公式（反引号包围）.

        Args:
            match_text: 匹配到的文本

        Returns:
            bool: 如果是ASCII公式则返回True
        """
        return (self.options.get('processascii', False) and
                match_text.startswith('`') and match_text.endswith('`'))

    def _extract_ascii_math_content(self, match_text: str) -> str:
        """提取ASCII数学公式内容并转换.

        Args:
            match_text: 完整的匹配文本（包含反引号）

        Returns:
            str: 处理后的数学公式文本
        """
        # 去除反引号
        ascii_content = match_text.strip('`')

        # 调用CCMATH的extract_asciimath方法
        try:
            ascii_latex = self.ccmath.extract_asciimath(ascii_content)
            return self.ccmath.wrap_math_md(ascii_latex)
        except Exception:
            # 如果解析失败，直接返回原内容作为LaTeX
            return self.ccmath.wrap_math_md(ascii_content)

    def _detect_ascii_math(self, tree: HtmlElement) -> bool:
        """检测HTML中是否包含ASCIIMath相关脚本，如果有，则开启processascii.

        Args:
            tree: HTML元素树

        Returns:
            bool: 如果检测到ASCIIMath脚本则返回True，否则返回False
        """
        # 重置processascii为默认值
        processascii = MATHJAX_OPTIONS.get('processascii', False)

        for script in tree.iter('script'):
            src = script.get('src', '')
            # 检查html是否包含ASCIIMathML.js等相关脚本
            if any(keyword in src for keyword in ASCIIMATH_KEYWORDS):
                processascii = True
                break

        return processascii


class MathJaxRenderMock(MathJaxRender):
    """虚拟的MathJax渲染器，用于没有MathJax配置但需要使用MathJax解析逻辑的情况.

    这个类主要用于处理以下场景：
    1. 网页中没有显式的MathJax配置（如<script type="text/x-mathjax-config">）
    2. 但在HTML解析过程中检测到了数学公式元素（如<math>标签、公式相关的class等）
    3. 需要使用MathJax渲染器方案扫一遍所有内容，防止漏抽取公式

    与普通MathJaxRender的区别：
    - MathJaxRender：会解析HTML中的MathJax配置，使用自定义的分隔符和选项
    - MathJaxRenderMock：直接使用默认的MathJax配置，不解析HTML配置
    """

    def __init__(self):
        """初始化虚拟MathJax渲染器."""
        super().__init__()
        self.render_type = MathRenderType.MATHJAX_MOCK
        # 使用默认的MathJax选项
        self.options = MATHJAX_OPTIONS.copy()

    def get_options(self, html: str) -> Dict[str, Any]:
        """虚拟渲染器直接返回默认选项，不解析HTML配置.

        Args:
            html: HTML字符串（忽略）

        Returns:
            Dict[str, Any]: 默认MathJax选项字典
        """
        return self.options

    def is_customized_options(self) -> bool:
        """虚拟渲染器始终返回False，表示使用默认配置."""
        return False


# 使用示例
if __name__ == '__main__':
    # MathJax示例
    mathjax_html = """
    <html>
    <head>
        <script type="text/x-mathjax-config">
            MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                },
                extensions: ["tex2jax.js", "TeX/AMSmath.js", "TeX/AMSsymbols.js"]
            });
        </script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-MML-AM_CHTML"></script>
    </head>
    <body>
        <p>Inline math: $E=mc^2$</p>
        <p>Display math: $$F = G\\frac{m_1 m_2}{r^2}$$</p>
    </body>
    </html>
    """

    # 测试MathJax
    print('Testing MathJax detection:')
    mathjax_tree = html_to_element(mathjax_html)
    render_type = BaseMathRender.detect_render_type(mathjax_tree)
    print(f'Detected render type: {render_type}')

    mathjax_render = BaseMathRender.create_render(mathjax_tree)
    if mathjax_render:
        options = mathjax_render.get_options(mathjax_html)
        print(f'MathJax options: {options}')
    else:
        print('No renderer detected')

    # # 测试find_math方法
    # print('\n测试find_math方法 - MathJax:')
    # mathjax_html = open('tests/llm_web_kit/extractor/html/recognizer/assets/ccmath/math_physicsforums.html', 'r').read()
    # mathjax_tree = html_to_element(mathjax_html)
    # mathjax_render = BaseMathRender.create_render(mathjax_tree)
    # print(f'mathjax_render options: {mathjax_render.get_options(mathjax_html)}')
    # if mathjax_render:
    #     # 处理前的HTML
    #     print('处理前的HTML:')
    #     print(element_to_html(mathjax_tree)[:500] + '...')

    #     # 使用find_math处理数学公式
    #     mathjax_render.find_math(mathjax_tree)

    #     # 处理后的HTML
    #     print('\n处理后的HTML:')
    #     processed_html = element_to_html(mathjax_tree)
    #     print(processed_html[:500] + '...')

    #     # 查找处理后的ccmath节点
    #     ccmath_nodes = mathjax_tree.xpath('.//*[self::ccmath-inline or self::ccmath-interline]')
    #     print(f'\n找到 {len(ccmath_nodes)} 个数学公式节点:')
    #     for i, node in enumerate(ccmath_nodes, 1):
    #         print(f"{i}. <{node.tag}> {node.text[:30]}{'...' if len(node.text) > 30 else ''}")

    # # 测试[tex]...[/tex]格式的数学公式
    # print('\n测试[tex]...[/tex]格式的数学公式:')
    # tex_html = '''
    # <html>
    # <body>
    #     <p>where [tex]d^2(x_1,x_2)[/tex] is the squared distance between [tex]x_1[/tex] and [tex]x_2[/tex] in some metric space [tex]\\Theta[/tex]. All integrals are over [tex]\\Theta[/tex]</p>
    # </body>
    # </html>
    # '''

    # tex_tree = html_to_element(tex_html)
    # mathjax_render = MathJaxRender()  # 直接创建MathJax渲染器，不需要检测

    # # 处理前的HTML
    # print('处理前的HTML:')
    # print(element_to_html(tex_tree))

    # # 使用find_math处理数学公式
    # mathjax_render.find_math(tex_tree)

    # # 处理后的HTML
    # print('\n处理后的HTML:')
    # processed_html = element_to_html(tex_tree)
    # print(processed_html)

    # # 查找处理后的ccmath节点
    # ccmath_nodes = tex_tree.xpath('.//*[self::ccmath-inline or self::ccmath-interline]')
    # print(f'\n找到 {len(ccmath_nodes)} 个数学公式节点:')
    # for i, node in enumerate(ccmath_nodes, 1):
    #     print(f'{i}. <{node.tag}> {node.text}')

    # # 测试真实文本
    # print('\n测试真实文本:')
    # real_text = '''
    # <p>where [tex]d^2(x_1,x_2)[/tex] is the $a=b$ squared distance between [tex]x_1[/tex] and [tex]x_2[/tex] in some metric space [tex]\\Theta[/tex]. All integrals are over [tex]\\Theta[/tex]</p>
    # '''

    # real_tree = html_to_element(real_text)
    # mathjax_render = MathJaxRender()

    # # 处理前的HTML
    # print('处理前的HTML:')
    # print(element_to_html(real_tree))

    # # 使用find_math处理数学公式
    # mathjax_render.find_math(real_tree)

    # # 处理后的HTML
    # print('\n处理后的HTML:')
    # processed_html = element_to_html(real_tree)
    # print(processed_html)

    # # 查找处理后的ccmath节点
    # ccmath_nodes = real_tree.xpath('.//*[self::ccmath-inline or self::ccmath-interline]')
    # print(f'\n找到 {len(ccmath_nodes)} 个数学公式节点:')
    # for i, node in enumerate(ccmath_nodes, 1):
    #     print(f'{i}. <{node.tag}> {node.text}')

    # # 测试$$格式的公式
    # print('\n专门测试$$格式的公式:')
    # dollar_text = '''
    # <p>This is a display formula: $$F = G\\frac{m_1 m_2}{r^2}$$</p>
    # '''

    # dollar_tree = html_to_element(dollar_text)
    # mathjax_render = MathJaxRender()

    # # 处理前的HTML
    # print('处理前的HTML:')
    # print(element_to_html(dollar_tree))

    # # 使用find_math处理数学公式
    # mathjax_render.find_math(dollar_tree)

    # # 处理后的HTML
    # print('\n处理后的HTML:')
    # processed_html = element_to_html(dollar_tree)
    # print(processed_html)

    # # 查找处理后的ccmath节点
    # ccmath_nodes = dollar_tree.xpath('.//*[self::ccmath-inline or self::ccmath-interline]')
    # print(f'\n找到 {len(ccmath_nodes)} 个数学公式节点:')
    # for i, node in enumerate(ccmath_nodes, 1):
    #     print(f'{i}. <{node.tag}> {node.text}')

    # empty_text = '''<div>Inline: \\(a^2 + b^2 = c^2\\) and display: \\[a^2 + b^2 = c^2\\]</div>'''
    # empty_tree = html_to_element(empty_text)
    # mathjax_render = MathJaxRender()
    # mathjax_render.find_math(empty_tree)
    # print(f'empty_tree: {element_to_html(empty_tree)}')
