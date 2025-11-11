import logging
import os
import re
from pathlib import Path
from typing import List, Tuple

from lxml import etree

# 在导入前就设置严格的日志控制
logging.basicConfig(level=logging.WARNING, force=True)

# 设置py_asciimath的日志级别，完全禁用其日志输出
py_asciimath_logger = logging.getLogger('py_asciimath')
py_asciimath_logger.setLevel(logging.ERROR)
py_asciimath_logger.disabled = True

from py_asciimath.translator.translator import ASCIIMath2Tex

from llm_web_kit.extractor.html.recognizer.recognizer import CCTag
from llm_web_kit.libs.doc_element_type import DocElementType
from llm_web_kit.libs.html_utils import (build_cc_element, element_to_html,
                                         html_to_element)
from llm_web_kit.libs.text_utils import normalize_ctl_text

asciimath2tex = ASCIIMath2Tex(log=False)

color_regex = re.compile(r'\\textcolor\[.*?\]\{.*?\}')


MATH_KEYWORDS = [
    'MathJax',
    'mathjax',
    '<math',
    'math-container',
    'katex.min.css',
    'latex.php',
    'codecogs',
    'tex.cgi',
    'class="tex"',
    "class='tex'",
]

LATEX_IMAGE_CLASS_NAMES = [
    'latexcenter',
    'latex',
    'tex',
    'latexdisplay',
    'latexblock',
    'latexblockcenter',
]

LATEX_IMAGE_SRC_NAMES = [
    'codecogs.com',
    'latex.php',
    '/images/math/codecogs',
    'mimetex.cgi',
    'mathtex.cgi',
]

# ccmath标签，区分行内行间公式
CCMATH_INTERLINE = CCTag.CC_MATH_INTERLINE
CCMATH_INLINE = CCTag.CC_MATH_INLINE
CCMATH_HANDLE_FAILED = 'ccmath-failed'


# 数学标记语言
class MathType:
    LATEX = 'latex'
    MATHML = 'mathml'
    ASCIIMATH = 'asciimath'
    HTMLMATH = 'htmlmath'  # sub, sup, etc.


# node.text匹配结果：
class MathMatchRes:
    ALLMATCH = 'all_match'
    PARTIALMATCH = 'partial_match'
    NOMATCH = 'no_match'


class MATH_TYPE_PATTERN:
    INLINEMATH = 'inlineMath'
    DISPLAYMATH = 'displayMath'


# CSDN博客的KaTeX标签
class CSDN:
    INLINE = 'katex--inline'
    DISPLAY = 'katex--display'
    MATH = 'katex-mathml'
    DOMAIN = 'blog.csdn.net'


# 知乎的数学公式标签
class ZHIHU:
    MATH = 'ztext-math'
    DOMAIN = 'zhihu.com'


class MATHINSIGHT:
    DOMAIN = 'mathinsight.org'


# 行内行间公式，MathJax中一般也可以通过配置来区分行内行间公式
EQUATION_INLINE = DocElementType.EQUATION_INLINE
EQUATION_INTERLINE = DocElementType.EQUATION_INTERLINE
latex_config = {
    MATH_TYPE_PATTERN.INLINEMATH: [
        ['$', '$'],
        ['\\(', '\\)'],
        ['[itex]', '[/itex]'],  # 这个网站自定义的分割，https://www.physicsforums.com/threads/turning-to-a-single-logarithm-then-simply.269419/
    ],
    MATH_TYPE_PATTERN.DISPLAYMATH: [
        ['\\[', '\\]'],
        ['$$', '$$'],
        ['[tex]', '[/tex]'],  # 这个网站自定义的分割，https://www.physicsforums.com/threads/turning-to-a-single-logarithm-then-simply.269419/
        # ['\\begin{equation}', '\\end{equation}'],
        # ['\\begin{align}', '\\end{align}'],
        # ['\\begin{alignat}', '\\end{alignat}'],
        # ['\\begin{array}', '\\end{array}'],
        # 添加通用的begin/end匹配
        ['\\begin{.*?}', '\\end{.*?}'],
    ],
}

# 兼容一些网站有错误的公式起始结尾
MATH_MD_CUSTOM_CONFIG = {
    'mathhelpforum.com': [
        ['<br />', '\\<br />'],  # 使用双反斜杠
        ['<br />', '<br />'],
    ],
}

asciiMath_config = {
    MATH_TYPE_PATTERN.INLINEMATH: [
        [r'`', r'`'],
    ],
    MATH_TYPE_PATTERN.DISPLAYMATH: [
        [r'`', r'`'],
    ],
}

MATH_TYPE_TO_DISPLAY = {
    MathType.LATEX: latex_config,
    MathType.ASCIIMATH: asciiMath_config
}


def text_strip(text):
    return text.strip() if text else text


xsl_path = os.path.join(Path(__file__).parent, 'mmltex/mmltex.xsl')
xslt = etree.parse(xsl_path)
transform = etree.XSLT(xslt)


def MATHINSIGHT_convert_to_standard_latex(text):
    """将MathInsight网站使用的自定义LaTeX宏转换为标准LaTeX格式。

    基于 https://mathinsight.org/static/mathjaxconfig/midefault.js?rev=2.6.1 配置文件中定义的宏。

    当前支持的转换：
    - 向量表示、雅可比矩阵
    - 微分和多阶微分、偏微分和多阶偏微分、范数
    - 各种积分形式（线积分、面积分、闭合积分等）
    - 参数化积分（线积分、面积分等）
    - 特殊函数符号（div、curl、tr）、默认字母和符号、集合符号
    - 换行和格式控制、颜色标记

    Args:
        text: 包含MathInsight宏的LaTeX文本

    Returns:
        转换后的标准LaTeX文本
    """
    replacements = {
        # 向量表示
        r'\\vc{([^}]*)}': r'\\mathbf{\1}',

        # 微分和偏微分
        r'\\diff{([^}]*)}{([^}]*)}': r'\\frac{\\mathrm{d} \1}{\\mathrm{d} \2}',
        r'\\diffn{([^}]*)}{([^}]*)}{([^}]*)}': r'\\frac{\\mathrm{d}^{\3} \1}{\\mathrm{d} \2^{\3}}',
        r'\\pdiff{([^}]*)}{([^}]*)}': r'\\frac{\\partial \1}{\\partial \2}',
        r'\\pdiffn{([^}]*)}{([^}]*)}{([^}]*)}': r'\\frac{\\partial^{\3} \1}{\\partial \2^{\3}}',

        # 矩阵和行列式
        r'\\jacm{([^}]*)}': r'D\1',
        r'\\JacobianMatrix{([^}]*)}': r'D\1',

        # 范数
        r'\\norm{([^}]*)}': r'\\|\1\\|',

        # 线积分
        r'\\lint{([^}]*)}{([^}]*)}': r'\\int_{\1} \2 \\cdot d\\mathbf{s}',
        r'\\clint{([^}]*)}{([^}]*)}': r'\\oint_{\1} \2 \\cdot d\\mathbf{s}',
        r'\\slint{([^}]*)}{([^}]*)}': r'\\int_{\1} \2 \\,ds',
        r'\\cslint{([^}]*)}{([^}]*)}': r'\\oint_{\1} \2 \\,ds',

        # 面积分
        r'\\sint{([^}]*)}{([^}]*)}': r'\\iint_{\1} \2 \\cdot d\\mathbf{S}',
        r'\\ssint{([^}]*)}{([^}]*)}': r'\\iint_{\1} \2 \\,dS',

        # 参数化积分（线积分）
        r'\\plint{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}': r'\\int_{\1}^{\2} \3(\4(t)) \\cdot \4\'(t) dt',
        r'\\pslint{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}': r'\\int_{\1}^{\2} \3(\4(t)) \\|\\4\'(t)\\| dt',

        # 参数化积分（面积分）
        r'\\psint{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\int_{\1}^{\2}\\int_{\3}^{\4} \5(\6(\7,\8)) \\cdot \\left( \\frac{\\partial \6}{\\partial \7}(\7,\8) \\times \\frac{\\partial \6}{\\partial \8}(\7,\8) \\right) d\7\\,d\8',

        r'\\psintrn{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\int_{\1}^{\2}\\int_{\3}^{\4} \5(\6(\7,\8)) \\cdot \\left( \\frac{\\partial \6}{\\partial \8}(\7,\8) \\times \\frac{\\partial \6}{\\partial \7}(\7,\8) \\right) d\7\\,d\8',

        r'\\psintrnro{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\int_{\1}^{\2}\\int_{\3}^{\4} \5(\6(\7,\8)) \\cdot \\left( \\frac{\\partial \6}{\\partial \8}(\7,\8) \\times \\frac{\\partial \6}{\\partial \7}(\7,\8) \\right) d\8\\,d\7',

        r'\\psintro{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\int_{\1}^{\2}\\int_{\3}^{\4} \5(\6(\7,\8)) \\cdot \\left( \\frac{\\partial \6}{\\partial \7}(\7,\8) \\times \\frac{\\partial \6}{\\partial \8}(\7,\8) \\right) d\8\\,d\7',

        r'\\psintor{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\iint_{\1} \2(\3(\4,\5)) \\cdot \\left( \\frac{\\partial \3}{\\partial \4}(\4,\5) \\times \\frac{\\partial \3}{\\partial \5}(\4,\5) \\right) d\4\\,d\5',

        # 参数化标量面积分
        r'\\pssint{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\int_{\1}^{\2}\\int_{\3}^{\4} \5(\6(\7,\8)) \\left\\| \\frac{\\partial \6}{\\partial \7}(\7,\8) \\times \\frac{\\partial \6}{\\partial \8}(\7,\8) \\right\\| d\7\\,d\8',

        r'\\pssintro{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\int_{\1}^{\2}\\int_{\3}^{\4} \5(\6(\7,\8)) \\left\\| \\frac{\\partial \6}{\\partial \7}(\7,\8) \\times \\frac{\\partial \6}{\\partial \8}(\7,\8) \\right\\| d\8\\,d\7',

        r'\\pssintor{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}{([^}]*)}':
            r'\\iint_{\1} \2(\3(\4,\5)) \\left\\| \\frac{\\partial \3}{\\partial \4}(\4,\5) \\times \\frac{\\partial \3}{\\partial \5}(\4,\5) \\right\\| d\4\\,d\5',

        # 特殊函数
        r'\\div': r'\\mathop{\\text{div}}',
        r'\\curl': r'\\mathop{\\text{curl}}',
        r'\\tr': r'\\mathop{\\rm tr}',

        # 默认字母替换
        r'\\dlvf': r'\\mathbf{F}',
        r'\\dlvfc': r'F',
        r'\\adlvf': r'\\mathbf{G}',
        r'\\adlvfc': r'G',
        r'\\dlc': r'C',
        r'\\adlc': r'B',
        r'\\sadlc': r'E',
        r'\\dlsi': r'f',
        r'\\dlr': r'D',
        r'\\dlv': r'W',
        r'\\dls': r'S',
        r'\\dlpf': r'f',  # 势函数

        # 参数化
        r'\\dllp': r'\\mathbf{c}',
        r'\\dllpc': r'c',
        r'\\adllp': r'\\mathbf{p}',
        r'\\adllpc': r'p',
        r'\\sadllp': r'\\mathbf{q}',
        r'\\sadllpc': r'q',
        r'\\tadllp': r'\\mathbf{d}',
        r'\\tadllpc': r'd',
        r'\\dlsp': r'\\mathbf{\\Phi}',
        r'\\dlspc': r'\\Phi',

        # 参数变量
        r'\\spfv': r'u',
        r'\\spsv': r'v',
        r'\\cvarf': r'\\mathbf{T}',
        r'\\cvarfc': r'T',
        r'\\cvarfv': r'u',
        r'\\cvarsv': r'v',
        r'\\cvartv': r'w',

        # 集合符号
        r'\\R': r'\\mathbb{R}',

        # 弧长和曲面符号
        r'\\als': r's',
        r'\\lis': r'\\mathbf{s}',
        r'\\sas': r'S',
        r'\\sid': r'\\mathbf{S}',

        # 不可见运算符
        r'\\invisibletimes': r'\\unicode{x2062}',
        r'\\cdotbadbreak': r'\\mmlToken{mo}[linebreak="badbreak"]{\\u22C5}',
        r'\\timesbadbreak': r'\\mmlToken{mo}[linebreak="badbreak"]{\\u00D7}',

        # 颜色标记
        r'\\blue': r'\\color{blue}{\\textbf{blue}}',
        r'\\red': r'\\color{red}{\\textbf{red}}',
        r'\\green': r'\\color{green}{\\textbf{green}}',
        r'\\cyan': r'\\color{cyan}{\\textbf{cyan}}',
        r'\\magenta': r'\\color{magenta}{\\textbf{magenta}}',

        # 换行控制
        r'\\goodbreak': r'\\mmlToken{mo}[linebreak="goodbreak"]{}',
        r'\\badbreak{([^}]*)}': r'\\mmlToken{mo}[linebreak="badbreak"]{\1}',
        r'\\nobreak{([^}]*)}': r'\\mmlToken{mo}[linebreak="nobreak"]{\1}',
    }

    # 应用所有替换规则
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    # 处理默认组合的积分形式
    default_combos = {
        # 默认线积分组合
        r'\\dlint': r'\\int_{C} \\mathbf{F} \\cdot d\\mathbf{s}',
        r'\\dclint': r'\\oint_{C} \\mathbf{F} \\cdot d\\mathbf{s}',
        r'\\dslint': r'\\int_{C} f \\,ds',
        r'\\dcslint': r'\\oint_{C} f \\,ds',

        # 默认面积分组合
        r'\\dsint': r'\\iint_{S} \\mathbf{F} \\cdot d\\mathbf{S}',
        r'\\dssint': r'\\iint_{S} f \\,dS',

        # 默认参数化积分组合
        r'\\dplint': r'\\int_{a}^{b} \\mathbf{F}(\\mathbf{c}(t)) \\cdot \\mathbf{c}\'(t) dt',
        r'\\dpslint': r'\\int_{a}^{b} f(\\mathbf{c}(t)) \\|\\mathbf{c}\'(t)\\| dt',
        r'\\dpsint': r'\\iint_{D} \\mathbf{F}(\\mathbf{\\Phi}(u,v)) \\cdot \\left( \\frac{\\partial \\mathbf{\\Phi}}{\\partial u}(u,v) \\times \\frac{\\partial \\mathbf{\\Phi}}{\\partial v}(u,v) \\right) du\\,dv',
        r'\\dpssint': r'\\iint_{D} f(\\mathbf{\\Phi}(u,v)) \\left\\| \\frac{\\partial \\mathbf{\\Phi}}{\\partial u}(u,v) \\times \\frac{\\partial \\mathbf{\\Phi}}{\\partial v}(u,v) \\right\\| du\\,dv',
    }

    for pattern, replacement in default_combos.items():
        text = re.sub(pattern, replacement, text)

    return text


class CCMATH():
    def __init__(self):
        self.url = ''

    def wrap_math_md(self, s):
        """去掉latex公式头尾的$$或$或\\(\\)或\\[\\]"""
        if not s:
            return s
        s = s.strip()
        s = normalize_ctl_text(s)
        if s.startswith('$$') and s.endswith('$$'):
            return s.replace('$$', '').strip()
        if s.startswith('$') and s.endswith('$'):
            return s.replace('$', '').strip()
        if s.startswith('\\(') and s.endswith('\\)'):
            return s.replace('\\(', '').replace('\\)', '').strip()
        if s.startswith('\\[') and s.endswith('\\]'):
            return s.replace('\\[', '').replace('\\]', '').strip()
        if s.startswith('`') and s.endswith('`'):
            return s.replace('`', '').strip()
        s = self.wrap_math_md_custom(s)
        # 处理MathInsight网站的特殊宏
        if MATHINSIGHT.DOMAIN in self.url:
            s = MATHINSIGHT_convert_to_standard_latex(s)
        return s.strip()

    # 循环MATH_MD_CUSTOM_CONFIG，如果url匹配，则去掉特殊网站的公式奇怪的起始结尾
    def wrap_math_md_custom(self, s):
        """去掉特殊网站的公式奇怪的起始结尾."""
        for url, config in MATH_MD_CUSTOM_CONFIG.items():
            if url in self.url:
                for start, end in config:
                    if s.startswith(start) and s.endswith(end):
                        # 去除 start 和 end
                        s = s[len(start):-len(end)]
        return s

    def wrap_math_space(self, s):
        """转义空格."""
        s = s.strip()
        return s.replace('&space;', ' ')

    def extract_asciimath(self, s: str) -> str:
        parsed = asciimath2tex.translate(s)
        return parsed

    def get_equation_type(self, html: str) -> List[Tuple[str, str]]:
        """根据latex_config判断数学公式是行内还是行间公式.

        Args:
            html: 包含数学公式的HTML文本

        Returns:
            Tuple[str, str]: (EQUATION_INLINE 或 EQUATION_INTERLINE, 公式类型)

        Examples:
            >>> get_equation_type("<span>这是行内公式 $x^2$ 测试</span>")
            ('equation-inline', 'latex')
            >>> get_equation_type("<span>这是行间公式 $$y=mx+b$$ 测试</span>")
            ('equation-interline', 'latex')
        """

        def check_delimiters(delims_list, s):
            for start, end in delims_list:
                escaped_start = re.escape(start)
                if start == '$':
                    escaped_start = r'(?<!\$)' + escaped_start + r'(?!\$)'
                # 处理end的特殊情况：如果是$，同样添加环视断言
                escaped_end = re.escape(end)
                if end == '$':
                    escaped_end = r'(?<!\$)' + escaped_end + r'(?!\$)'
                all_pattern = f'^{escaped_start}.*?{escaped_end}$'.replace(r'\.\*\?', '.*?')
                partial_pattern = f'{escaped_start}.*?{escaped_end}'.replace(r'\.\*\?', '.*?')
                if re.search(all_pattern, s, re.DOTALL):
                    return MathMatchRes.ALLMATCH
                if re.search(partial_pattern, s, re.DOTALL):
                    return MathMatchRes.PARTIALMATCH
            return MathMatchRes.NOMATCH

        tree = html_to_element(html)
        if tree is None:
            raise ValueError(f'Failed to load html: {html}')
        result = []
        for node in tree.iter():
            # 先检查mathml
            math_elements = node.xpath('//math | //*[contains(local-name(), ":math")]')
            if len(math_elements) > 0:
                # 检查math标签是否有display属性且值为block，https://developer.mozilla.org/en-US/docs/Web/MathML/Element/math
                if math_elements[0].get('display') == 'block':
                    result.append((EQUATION_INTERLINE, MathType.MATHML))
                else:
                    # 检查math下的mstyle标签，https://developer.mozilla.org/en-US/docs/Web/MathML/Element/mstyle
                    # math_mstyle_element = math_elements[0].xpath('.//mstyle')
                    # if math_mstyle_element and math_mstyle_element[0].get('displaystyle') == 'true':
                    #     return EQUATION_INTERLINE, MathType.MATHML
                    result.append((EQUATION_INLINE, MathType.MATHML))

            # 再检查latex
            if text := text_strip(node.text):
                # 优先检查行间公式
                if check_delimiters(latex_config[MATH_TYPE_PATTERN.DISPLAYMATH], text) != MathMatchRes.NOMATCH:
                    result.append((EQUATION_INTERLINE, MathType.LATEX))
                if check_delimiters(latex_config[MATH_TYPE_PATTERN.INLINEMATH], text) != MathMatchRes.NOMATCH:
                    result.append((EQUATION_INLINE, MathType.LATEX))

                # 再检查asciimath，通常被包含在`...`中，TODO：先只支持行间公式
                if check_delimiters(asciiMath_config[MATH_TYPE_PATTERN.DISPLAYMATH], text) == MathMatchRes.ALLMATCH:
                    result.append((EQUATION_INTERLINE, MathType.ASCIIMATH))
                if check_delimiters(asciiMath_config[MATH_TYPE_PATTERN.DISPLAYMATH], text) == MathMatchRes.PARTIALMATCH:
                    result.append((EQUATION_INLINE, MathType.ASCIIMATH))

            # 检查script标签
            script_elements = tree.xpath('//script')
            if script_elements and any(text_strip(elem.text) for elem in script_elements):
                # 判断type属性，如有包含 mode=display 则认为是行间公式
                for script in script_elements:
                    if 'mode=display' in script.get('type', ''):
                        result.append((EQUATION_INTERLINE, MathType.LATEX))
                    else:
                        result.append((EQUATION_INLINE, MathType.LATEX))

            # 检查 HTML 数学标记（sub 和 sup）
            sub_elements = tree.xpath('//sub')
            sup_elements = tree.xpath('//sup')
            if (sub_elements and any(text_strip(elem.text) for elem in sub_elements)) or \
                (sup_elements and any(text_strip(elem.text) for elem in sup_elements)):
                result.append((EQUATION_INLINE, MathType.HTMLMATH))

            # 检查当前节点是否是katex元素（CSDN）
            if CSDN.DOMAIN in self.url and node.tag == 'span' and node.get('class'):
                node_class = node.get('class')
                if CSDN.INLINE in node_class:
                    result.append((EQUATION_INLINE, MathType.LATEX))
                elif CSDN.DISPLAY in node_class:
                    result.append((EQUATION_INTERLINE, MathType.LATEX))
        return self.equation_type_to_tag(result)

    def equation_type_to_tag(self, type_math_type: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        return list({
            (eq_type, math_type): (
                CCMATH_INLINE if eq_type == EQUATION_INLINE else CCMATH_INTERLINE,
                math_type
            )
            for eq_type, math_type in type_math_type
            if eq_type in {EQUATION_INLINE, EQUATION_INTERLINE}
        }.values())

    def mml_to_latex(self, mml_code):
        # Remove any attributes from the math tag
        mml_ns = re.sub(r'<math.*?>', '<math xmlns="http://www.w3.org/1998/Math/MathML">', mml_code)
        # mml_ns = mml_code
        mml_ns = mml_ns.replace('&quot;', '"')
        mml_ns = mml_ns.replace("'\\\"", '"').replace("\\\"'", '"')

        pattern = r'"([^"]+?)\''
        mml_ns = re.sub(pattern, r'"\1"', mml_ns)
        mml_ns = re.sub(r'<mspace[^>]*>.*?</mspace>', '', mml_ns, flags=re.DOTALL)
        # 先将mml_ns转换为HtmlElement，兼容一些有错误的html解析
        mml_dom = html_to_element(mml_ns)
        # 再将 HtmlElement 转换为 etree._Element 以兼容 XSLT 转换
        mml_str = etree.tostring(mml_dom)
        # 提前修复已知的一些利用XSLT方法转换的错误
        mml_str = self.fix_mathml_superscript(mml_str)
        mml_element = etree.fromstring(mml_str)
        mmldom = transform(mml_element)
        latex_code = str(mmldom)
        # print(f'Processing MathML: {etree.tostring(mml_element, encoding="unicode", pretty_print=True)}')
        # print(f'After XSLT transformation: {str(mmldom)}')
        # print(f'latex_code: {latex_code}')
        return latex_code

    def fix_mathml_superscript(self, mathml_str):
        # 解析输入的MathML字符串
        root = etree.fromstring(mathml_str)
        namespace = {'m': 'http://www.w3.org/1998/Math/MathML'}
        mathml_ns = namespace['m']
        for msup in root.xpath('//m:msup', namespaces=namespace):
            if len(msup) < 1:
                continue
            base = msup[0]
            if base.tag != f'{{{mathml_ns}}}mo' or base.text != ')':
                continue
            parent = msup.getparent()
            if parent is None:
                continue
            siblings = list(parent)
            msup_index = siblings.index(msup)
            left_paren = None
            for i in range(msup_index - 1, -1, -1):
                node = siblings[i]
                if node.tag == f'{{{mathml_ns}}}mo' and node.text == '(':
                    left_paren = i
                    break
            if left_paren is None:
                continue
            content_nodes = siblings[left_paren:msup_index]
            mrow = etree.Element(f'{{{mathml_ns}}}mrow')
            for node in content_nodes:
                parent.remove(node)
                mrow.append(node)
            new_msup = etree.Element(f'{{{mathml_ns}}}msup')
            new_msup.append(mrow)
            if len(msup) >= 2:
                new_msup.extend(msup[1:])
            mrow.append(base)
            parent.insert(left_paren, new_msup)
            parent.remove(msup)
        return etree.tostring(root, encoding='unicode', pretty_print=True)

    def build_cc_exception_tag(self, text, math_type, math_render) -> str:
        return element_to_html(build_cc_element(
            html_tag_name=CCMATH_HANDLE_FAILED,
            text=text,
            tail='',
            type=math_type,
            by=math_render,
            html=text
        ))


if __name__ == '__main__':
    cm = CCMATH()
    print(cm.get_equation_type('<span>$$a^2 + b^2 = c^2$$</span>'))
    print(cm.get_equation_type('<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mi>a</mi><mo>&#x2260;</mo><mn>0</mn></math>'))
    print(cm.get_equation_type('<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>a</mi><mo>&#x2260;</mo><mn>0</mn></math>'))
    print(cm.get_equation_type('<p>这是p的text</p>'))
    # print(cm.get_equation_type(r'<p>[tex]\frac{1}{4} Log(x-1)=Log((x-1)^{1\over{4}})= Log(\sqrt[4]{x-1})[/tex]</p>'))
    # print(cm.get_equation_type(r'<p>abc [itex]x^2[/itex] abc</p>'))
    # print(cm.get_equation_type(r'<p>abc [itex]x^2 abc</p>'))
    print(cm.get_equation_type(r'<p>\begin{align} a^2+b=c\end{align}</p>'))
    print(cm.get_equation_type(r'<p>\begin{abc} a^2+b=c\end{abc}</p>'))
    print(cm.wrap_math_md(r'{\displaystyle \operatorname {Var} (X)=\operatorname {E} \left[(X-\mu)^{2}\right].}'))
    print(cm.wrap_math_md(r'$$a^2 + b^2 = c^2$$'))
    print(cm.wrap_math_md(r'\(a^2 + b^2 = c^2\)'))
    print(cm.extract_asciimath('x=(-b +- sqrt(b^2 - 4ac))/(2a)'))
    print(cm.replace_math('ccmath-interline','asciimath','',html_to_element(r'<p>`x=(-b +- sqrt(b^2 - 4ac))/(2a)`</p>'),None,True))
    print(cm.replace_math('ccmath-interline','asciimath','',html_to_element(r'<p>like this: \`E=mc^2\`</p>'),None,True))
    print(cm.replace_math('ccmath-interline','asciimath','',html_to_element(r'<p>A `3xx3` matrix,`((1,2,3),(4,5,6),(7,8,9))`, and a `2xx1` matrix, or vector, `((1),(0))`.</p>'),None,True))
    print(cm.replace_math('ccmath-interline','asciimath','',html_to_element(r'<p>`(x+1)/x^2``1/3245`</p>'),None,True))
    print(cm.replace_math('ccmath-interline','latex','',html_to_element(r'<p>start $$f(a,b,c) = (a^2+b^2+c^2)^3$$end</p>'),None,False))
    print(cm.replace_math('ccmath-inline','latex','',html_to_element(r'<p>\( \newcommand{\norm}[1]{\| #1 \|}\)</p>'),None,False))
    # cm.url = 'mathhelpforum.com'
    # print(cm.wrap_math_md_custom(r'<br />\begin{align} a^2+b=c\end{align}\<br />'))
    # print(cm.wrap_math_md_custom(r'<br />dz=\frac{1}{2}\frac{dx}{\cos ^2 x}<br />'))
