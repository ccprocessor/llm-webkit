#!/usr/bin/env python3
"""全面测试新的simple.py API，整合原有测试场景."""

import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from llm_web_kit.exception.exception import InvalidOutputFormatException
from llm_web_kit.simple import (ExtractorFactory, PipeTpl,
                                extract_content_from_html_with_layout_batch,
                                extract_content_from_html_with_llm,
                                extract_content_from_html_with_magic_html,
                                extract_content_from_main_html,
                                extract_main_html_only)


class TestSimple(unittest.TestCase):
    """Simple API的全面测试用例."""

    def setUp(self):
        """设置测试数据."""
        self.url = 'https://example.com'
        self.html_content = '<html><body><h1>Test Content</h1><p>This is a test paragraph.</p><img src="https://example.com/image.jpg" alt="Test Image" /></body></html>'

        # 原有测试中的复杂HTML内容
        self.real_html_content = """
        <!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML标签综合示例</title>

    <!-- 内嵌CSS样式 -->
    <style>
        /* 基础样式设置 */
        body {
            font-family: 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }

        /* 页眉样式 */
        header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            text-align: center;
        }

        /* 主体内容样式 */
        main {
            max-width: 800px;
            margin: 2rem auto;
            padding: 1rem;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        /* 交互按钮样式 */
        .action-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .action-btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <!-- 语义化页眉 -->
    <header>
        <h1>网页标题</h1>
        <nav>
            <ul style="list-style-type: none; display: flex; justify-content: center; gap: 1rem;">
                <li><a href="#" style="color: white; text-decoration: none;">首页</a></li>
                <li><a href="#" style="color: white; text-decoration: none;">关于</a></li>
            </ul>
        </nav>
    </header>

    <!-- 主体内容区域 -->
    <main>
        <article>
            <h2>文章标题</h2>
            <p>这是有效的文本内容，展示了如何在HTML文档中组织实际内容。</p>

            <!-- 带交互的元素 -->
            <button id="demoBtn" class="action-btn">点击演示</button>
            <div id="dynamicContent" style="margin-top: 1rem; display: none;">
                <p>这是通过JavaScript动态显示的内容！</p>
            </div>
        </article>
    </main>

    <!-- 页脚区域 -->
    <footer style="text-align: center; padding: 1rem; background-color: #34495e; color: white;">
        <p>© 2025 版权所有</p>
    </footer>

    <!-- 内嵌JavaScript -->
    <script>
        // 等待DOM加载完成
        document.addEventListener('DOMContentLoaded', function() {
            const demoBtn = document.getElementById('demoBtn');
            const dynamicContent = document.getElementById('dynamicContent');

            // 按钮点击事件处理
            demoBtn.addEventListener('click', function() {
                dynamicContent.style.display = 'block';
                this.textContent = '已显示内容';

                // 创建动态元素
                const newElement = document.createElement('p');
                newElement.textContent = '这是动态创建的元素！';
                newElement.style.color = '#e74c3c';
                dynamicContent.appendChild(newElement);
            });

            console.log('页面初始化完成');
        });
    </script>
</body>
</html>
        """

        self.main_html = '<div><body><h1>Test Content</h1><p>This is a test paragraph.</p><img src="https://example.com/image.jpg" alt="Test Image"></body></div>'
        self.expected_md = '# Test Content\n\nThis is a test paragraph.\n'
        self.expected_mm_md = '# Test Content\n\nThis is a test paragraph.\n\n![Test Image](e5db82b5bf63d49d80c5533616892d3386f43955369520986d67653c700fc53c)\n'
        self.expected_mm_md_raw_url = '# Test Content\n\nThis is a test paragraph.\n\n![Test Image](https://example.com/image.jpg)\n'
        self.base_path = os.path.dirname(os.path.abspath(__file__))

    # ========================================
    # 基础功能测试
    # ========================================

    def test_extract_html_to_md(self):
        """测试提取HTML到MD."""
        md = extract_content_from_html_with_magic_html(self.url, self.html_content)
        self.assertEqual(md, self.expected_md)

    def test_extract_html_to_mm_md(self):
        """测试提取HTML到MM_MD."""
        mm_md = extract_content_from_html_with_magic_html(self.url, self.html_content, 'mm_md')
        self.assertEqual(mm_md, self.expected_mm_md)

    def test_extract_magic_main_html(self):
        """测试提取main_html."""
        main_html = extract_main_html_only(self.url, self.html_content, PipeTpl.MAGIC_HTML)
        self.assertEqual(main_html, self.main_html)

    def test_extract_noclip(self):
        """测试从原始HTML直接提取内容."""
        md = extract_content_from_main_html(self.url, self.html_content)
        self.assertEqual(md, self.expected_md)

    def test_extract_noclip_mm_md(self):
        """测试从原始HTML直接提取内容."""
        md = extract_content_from_main_html(self.url, self.html_content, 'mm_md')
        self.assertEqual(md, self.expected_mm_md)

    def test_extract_main_html_only_default(self):
        """测试对外方法：extract_main_html_only默认使用MAGIC_HTML."""
        result = extract_main_html_only(self.url, self.html_content, language='en')
        self.assertEqual(result, self.main_html)

    def test_extract_content_from_main_html_default(self):
        """测试对外方法：extract_content_from_main_html默认md格式."""
        result = extract_content_from_main_html(self.url, self.main_html, language='en')
        self.assertEqual(result, self.expected_md)

    def test_extract_content_from_main_html_mm_md(self):
        """测试对外方法：extract_content_from_main_html输出mm_md格式."""
        result = extract_content_from_main_html(self.url, self.main_html, 'mm_md', language='en')
        self.assertEqual(result, self.expected_mm_md)

    def test_extract_content_from_html_with_llm(self):
        """测试对外方法：extract_content_from_html_with_llm."""
        result = extract_content_from_html_with_llm(self.url, self.html_content)
        self.assertIsInstance(result, str)

    def test_extract_content_from_html_with_layout_batch(self):
        """测试对外方法：extract_content_from_html_with_layout_batch."""
        result = extract_content_from_html_with_layout_batch(self.url, self.html_content)
        self.assertIsInstance(result, str)

    # ========================================
    # 测试异常处理
    # ========================================

    def test_invalid_extractor_type_exception(self):
        """测试无效的extractor类型异常."""
        with self.assertRaises(Exception):
            # 使用无效的管道模板名称
            ExtractorFactory.get_extractor('INVALID_TYPE')

    def test_invalid_output_format_exception(self):
        """测试无效的输出格式异常."""
        with self.assertRaises(InvalidOutputFormatException) as context:
            extract_content_from_main_html(self.url, self.main_html, 'INVALID_FORMAT')

        self.assertIn('Invalid output format', str(context.exception.custom_message))
        self.assertEqual(context.exception.error_code, 82000000)

    # ========================================
    # 测试不同输出格式
    # ========================================

    def test_output_format_md(self):
        """测试md输出格式."""
        result = extract_content_from_main_html(self.url, self.main_html, 'md', language='en')
        self.assertEqual(result, self.expected_md)

    def test_output_format_mm_md(self):
        """测试mm_md输出格式."""
        result = extract_content_from_main_html(self.url, self.main_html, 'mm_md', language='en')
        self.assertEqual(result, self.expected_mm_md)

    def test_output_format_json(self):
        """测试json输出格式."""
        result = extract_content_from_main_html(self.url, self.main_html, 'json')
        self.assertIsInstance(result, str)
        # JSON输出应该包含JSON结构
        self.assertTrue(result.startswith('{') or result.startswith('['))

    def test_language_option_affects_spacing_en(self):
        """测试 language='en' 时英文片段合并插入空格."""
        html_content = '<div><body><p><span>Hello</span><span>World</span></p></body></div>'
        md = extract_content_from_main_html(self.url, html_content, language='en')
        self.assertIn('Hello World', md)
        self.assertNotIn('HelloWorld', md)

    def test_language_option_affects_spacing_zh(self):
        """测试 language='zh' 时英文片段合并不插入空格（与中文等无分词语言一致策略）。"""
        html_content = '<div><body><p><span>Hello</span><span>World</span></p></body></div>'
        md = extract_content_from_main_html(self.url, html_content, language='zh')
        self.assertIn('HelloWorld', md)

    # ========================================
    # 测试ExtractorFactory缓存机制和线程安全
    # ========================================

    def test_extractor_factory_caching(self):
        """测试ExtractorFactory的缓存机制."""
        # 第一次获取
        extractor1 = ExtractorFactory.get_extractor(PipeTpl.MAGIC_HTML)

        # 第二次获取应该返回同一个实例（从缓存）
        extractor2 = ExtractorFactory.get_extractor(PipeTpl.MAGIC_HTML)

        self.assertIs(extractor1, extractor2, '应该返回同一个缓存的实例')

    def test_extractor_factory_different_pipe_tpls(self):
        """测试不同pipe_tpl会创建不同的extractor实例."""
        extractor1 = ExtractorFactory.get_extractor(PipeTpl.MAGIC_HTML)
        extractor2 = ExtractorFactory.get_extractor(PipeTpl.NOCLIP)

        self.assertIsNot(extractor1, extractor2, '不同pipe_tpl应该返回不同的实例')

    # ========================================
    # use_raw_image_url参数测试
    # ========================================

    def test_extract_content_from_main_html_with_raw_image_url(self):
        """测试extract_content_from_main_html使用原始图片URL."""
        result = extract_content_from_main_html(self.url, self.main_html, 'mm_md', 'en', use_raw_image_url=True)
        self.assertEqual(result, self.expected_mm_md_raw_url)

    def test_extract_content_from_html_with_magic_html_with_raw_image_url(self):
        """测试extract_content_from_html_with_magic_html使用原始图片URL."""
        result = extract_content_from_html_with_magic_html(self.url, self.html_content, 'mm_md', 'en', use_raw_image_url=True)
        self.assertEqual(result, self.expected_mm_md_raw_url)

    def test_extract_content_from_html_with_llm_with_raw_image_url(self):
        """测试extract_content_from_html_with_llm使用原始图片URL."""
        result = extract_content_from_html_with_llm(self.url, self.html_content, 'mm_md', 'en', use_raw_image_url=True)
        # 由于LLM可能有不同的处理结果，我们只验证包含原始URL
        self.assertIn('https://example.com/image.jpg', result)

    def test_extract_content_from_html_with_layout_batch_with_raw_image_url(self):
        """测试extract_content_from_html_with_layout_batch使用原始图片URL."""
        result = extract_content_from_html_with_layout_batch(self.url, self.html_content, 'mm_md', 'en', use_raw_image_url=True)
        # 由于layout_batch可能有不同的处理结果，我们只验证包含原始URL
        self.assertIn('https://example.com/image.jpg', result)

    def test_extract_content_from_main_html_without_raw_image_url(self):
        """测试extract_content_from_main_html不使用原始图片URL（默认行为）."""
        result = extract_content_from_main_html(self.url, self.main_html, 'mm_md', 'en', use_raw_image_url=False)
        self.assertEqual(result, self.expected_mm_md)
        # 确保不包含原始URL
        self.assertNotIn('https://example.com/image.jpg', result)

    def test_extract_content_from_html_with_magic_html_without_raw_image_url(self):
        """测试extract_content_from_html_with_magic_html不使用原始图片URL（默认行为）."""
        result = extract_content_from_html_with_magic_html(self.url, self.html_content, 'mm_md', 'en', use_raw_image_url=False)
        self.assertEqual(result, self.expected_mm_md)
        # 确保不包含原始URL
        self.assertNotIn('https://example.com/image.jpg', result)

    def test_use_raw_image_url_only_affects_mm_md_format(self):
        """测试use_raw_image_url参数只对mm_md格式有效，对其他格式无影响."""
        # 测试md格式不受影响
        result_md_false = extract_content_from_main_html(self.url, self.main_html, 'md', 'en', use_raw_image_url=False)
        result_md_true = extract_content_from_main_html(self.url, self.main_html, 'md', 'en', use_raw_image_url=True)
        self.assertEqual(result_md_false, result_md_true)
        self.assertEqual(result_md_false, self.expected_md)

        # 测试plain_md格式不受影响
        result_plain_md_false = extract_content_from_main_html(self.url, self.main_html, 'plain_md', 'en', use_raw_image_url=False)
        result_plain_md_true = extract_content_from_main_html(self.url, self.main_html, 'plain_md', 'en', use_raw_image_url=True)
        self.assertEqual(result_plain_md_false, result_plain_md_true)


class TestExtractorFactoryThreadSafety(unittest.TestCase):
    """ExtractorFactory线程安全性专项测试."""

    def setUp(self):
        """测试前清空缓存."""
        self.original_cache = ExtractorFactory._extractors.copy()
        ExtractorFactory._extractors.clear()

    def tearDown(self):
        """测试后恢复原始缓存."""
        ExtractorFactory._extractors.clear()
        ExtractorFactory._extractors.update(self.original_cache)

    def test_thread_safety_same_pipe_tpl(self):
        """测试多线程访问同一pipe_tpl的线程安全性."""
        results = []

        def get_extractor_worker(worker_id):
            """工作线程函数."""
            # 添加小延迟，增加竞态条件出现的概率
            time.sleep(0.01)
            extractor = ExtractorFactory.get_extractor(PipeTpl.MAGIC_HTML)
            results.append((worker_id, id(extractor)))
            return extractor

        # 使用10个线程同时访问
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(get_extractor_worker, i)
                futures.append(future)

            # 等待所有线程完成
            extractors = [future.result() for future in futures]

        # 验证所有extractor实例应该是同一个对象
        extractor_ids = [id(ext) for ext in extractors if ext is not None]
        unique_ids = set(extractor_ids)

        self.assertEqual(len(extractors), 10, '应该有10个extractor返回')
        self.assertEqual(len(unique_ids), 1, '所有线程应该获取到同一个extractor实例')
        self.assertEqual(len(ExtractorFactory._extractors), 1, '缓存中应该只有1个extractor')

        # 验证所有实例确实是同一个对象
        first_extractor = extractors[0]
        for extractor in extractors[1:]:
            self.assertIs(extractor, first_extractor, '所有extractor应该是同一个对象')

    def test_thread_safety_different_pipe_tpls(self):
        """测试多线程访问不同pipe_tpl的线程安全性."""
        results = {}  # 改用字典，以worker_id为key

        def get_extractor_worker(pipe_tpl, worker_id):
            """工作线程函数."""
            # 添加小延迟，增加竞态条件出现的概率
            time.sleep(0.01)
            extractor = ExtractorFactory.get_extractor(pipe_tpl)
            results[worker_id] = (pipe_tpl, extractor, id(extractor))
            return extractor

        # 使用多个线程访问不同的pipe_tpl
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            pipe_tpls = [PipeTpl.MAGIC_HTML, PipeTpl.NOCLIP, PipeTpl.MAGIC_HTML_NOCLIP]

            for i in range(6):
                pipe_tpl = pipe_tpls[i % len(pipe_tpls)]
                future = executor.submit(get_extractor_worker, pipe_tpl, i)
                futures.append(future)

        # 重新组织结果，确保索引匹配
        organized_results = []
        for i in range(6):
            pipe_tpl, extractor, extractor_id = results[i]
            organized_results.append((i, pipe_tpl, extractor, extractor_id))

        # 按pipe_tpl分组验证
        pipe_tpl_groups = {}
        for worker_id, pipe_tpl, extractor, extractor_id in organized_results:
            if pipe_tpl not in pipe_tpl_groups:
                pipe_tpl_groups[pipe_tpl] = []
            pipe_tpl_groups[pipe_tpl].append((worker_id, extractor, extractor_id))

        # 验证每个pipe_tpl组内的extractor是同一个实例
        for pipe_tpl, group_extractors in pipe_tpl_groups.items():
            if len(group_extractors) > 1:
                first_extractor = group_extractors[0][1]

                for worker_id, extractor, extractor_id in group_extractors[1:]:
                    self.assertIs(extractor, first_extractor,
                                 f'{pipe_tpl}类型的extractor应该是同一个实例 (Worker {worker_id})')

        # 验证缓存大小
        cache_size = len(ExtractorFactory._extractors)
        expected_cache_size = len(pipe_tpl_groups)

        self.assertLessEqual(cache_size, 3, '缓存中应该有3个extractor')
        self.assertEqual(cache_size, expected_cache_size, '缓存大小应该等于使用的pipe_tpl类型数量')


class TestSimpleEdgeCases(unittest.TestCase):
    """边缘情况测试类."""

    def setUp(self):
        """设置测试数据."""
        self.url = 'https://example.com'
        self.main_html = '<div><body><h1>Test Content</h1><p>This is a test paragraph.</p><img src="https://example.com/image.jpg" alt="Test Image"></body></div>'

    def test_empty_html_content(self):
        """测试空HTML内容."""
        # 空HTML会导致解析异常，这是预期的行为
        with self.assertRaises(Exception):
            extract_content_from_html_with_magic_html(self.url, '')

    def test_empty_main_html_for_stage2(self):
        """测试空main_html用于第二阶段."""
        # 空main_html会导致解析异常，这是预期的行为
        with self.assertRaises(Exception):
            extract_content_from_main_html(self.url, '')

    def test_malformed_html(self):
        """测试格式错误的HTML."""
        malformed_html = '<html><body><h1>Test<p>No closing tags'
        result = extract_content_from_html_with_magic_html(self.url, malformed_html)
        self.assertIsInstance(result, str)


class TestSimpleIntegration(unittest.TestCase):
    """集成测试和真实场景测试类."""

    def setUp(self):
        """设置测试数据."""
        self.url = 'https://example.com'
        self.html_content = '<html><body><h1>Test Content</h1><p>This is a test paragraph.</p><img src="https://example.com/image.jpg" alt="Test Image" /></body></html>'
        self.base_path = os.path.dirname(os.path.abspath(__file__))

        # 原有测试中的复杂HTML内容
        self.real_html_content = """
        <!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML标签综合示例</title>

    <!-- 内嵌CSS样式 -->
    <style>
        /* 基础样式设置 */
        body {
            font-family: 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }

        /* 页眉样式 */
        header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            text-align: center;
        }

        /* 主体内容样式 */
        main {
            max-width: 800px;
            margin: 2rem auto;
            padding: 1rem;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        /* 交互按钮样式 */
        .action-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .action-btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <!-- 语义化页眉 -->
    <header>
        <h1>网页标题</h1>
        <nav>
            <ul style="list-style-type: none; display: flex; justify-content: center; gap: 1rem;">
                <li><a href="#" style="color: white; text-decoration: none;">首页</a></li>
                <li><a href="#" style="color: white; text-decoration: none;">关于</a></li>
            </ul>
        </nav>
    </header>

    <!-- 主体内容区域 -->
    <main>
        <article>
            <h2>文章标题</h2>
            <p>这是有效的文本内容，展示了如何在HTML文档中组织实际内容。</p>

            <!-- 带交互的元素 -->
            <button id="demoBtn" class="action-btn">点击演示</button>
            <div id="dynamicContent" style="margin-top: 1rem; display: none;">
                <p>这是通过JavaScript动态显示的内容！</p>
            </div>
        </article>
    </main>

    <!-- 页脚区域 -->
    <footer style="text-align: center; padding: 1rem; background-color: #34495e; color: white;">
        <p>© 2025 版权所有</p>
    </footer>

    <!-- 内嵌JavaScript -->
    <script>
        // 等待DOM加载完成
        document.addEventListener('DOMContentLoaded', function() {
            const demoBtn = document.getElementById('demoBtn');
            const dynamicContent = document.getElementById('dynamicContent');

            // 按钮点击事件处理
            demoBtn.addEventListener('click', function() {
                dynamicContent.style.display = 'block';
                this.textContent = '已显示内容';

                // 创建动态元素
                const newElement = document.createElement('p');
                newElement.textContent = '这是动态创建的元素！';
                newElement.style.color = '#e74c3c';
                dynamicContent.appendChild(newElement);
            });

            console.log('页面初始化完成');
        });
    </script>
</body>
</html>
        """

    def test_extract_real_html_to_md(self):
        """测试真实HTML内容，验证JavaScript被过滤."""
        md = extract_content_from_main_html(self.url, self.real_html_content)
        self.assertNotIn('DOMContentLoaded', md)

    def test_extract_lack_item(self):
        """测试lack_item.html文件."""
        html_content = open(os.path.join(self.base_path, 'assets', 'lack_item.html'), 'r').read()
        md = extract_content_from_main_html(self.url, html_content)
        self.assertGreater(len(md), 0)

    def test_extract_lack_item_2(self):
        """测试lack_item_2.html文件."""
        html_content = open(os.path.join(self.base_path, 'assets', 'lack_item_2.html'), 'r').read()
        md = extract_content_from_main_html(self.url, html_content)
        # 验证提取到了主要内容
        self.assertIn('2001-2015 Physics Forums', md)

    def test_extract_word_press(self):
        """测试word_press.html文件."""
        html_content = open(os.path.join(self.base_path, 'assets', 'word_press.html'), 'r').read()
        md = extract_content_from_main_html(self.url, html_content)
        self.assertIn('For descriptions of the methods (AM1, HF, MP2, ...) a', md)

    def test_full_pipeline_integration(self):
        """测试完整的两阶段流水线."""
        # 第一阶段：提取main_html
        main_html = extract_main_html_only(self.url, self.real_html_content, language='en')
        self.assertIsInstance(main_html, str)
        self.assertTrue(len(main_html) > 0)

        # 第二阶段：从main_html提取内容
        markdown = extract_content_from_main_html(self.url, main_html, language='en')
        self.assertIsInstance(markdown, str)
        self.assertTrue(len(markdown) > 0)

        # 对比直接两阶段调用的结果
        direct_result = extract_content_from_html_with_magic_html(self.url, self.real_html_content, language='en')
        self.assertEqual(markdown, direct_result, "分步骤处理和直接处理的结果应该一致")

    def test_multiple_calls_consistency(self):
        """测试多次调用的一致性."""
        results = []
        for _ in range(3):
            result = extract_content_from_html_with_magic_html(self.url, self.html_content)
            results.append(result)

        # 所有结果应该相同
        self.assertTrue(all(r == results[0] for r in results))

    def test_filter_display_none_content(self):
        """测试display:none的内容是否被正确过滤."""
        html_content = '''<html><body>
        <div class="options-div-0-0 option-box__items" style="display: none;">
            <span class="bedroom-rate__title">Room Only Rate</span>
            <span class="bedroom-rate__price">£1,230.00</span>
        </div>
        <p>正常内容</p>
        </body></html>'''

        # 使用MAGIC_HTML_NOCLIP模拟原来的clip_html=False
        md = extract_content_from_main_html(self.url, html_content)

        # 验证隐藏内容被过滤掉了
        self.assertNotIn('Room Only Rate', md)
        self.assertNotIn('£1,230.00', md)

        # 验证正常内容被保留
        self.assertIn('正常内容', md)

    def test_extract_main_html_with_script(self):
        """测试main_html中包含script标签的情况."""
        html_content = open(os.path.join(self.base_path, 'assets', 'main_html_with_script.html'), 'r').read()
        md = extract_content_from_main_html(self.url, html_content)
        self.assertIn('A. What are the cultural factors which make expansion abroad in retailing difficult?', md)
        self.assertIn('B. How does the TV advertising campaign initiated by IKEA overcome the entry barrier of high advertising expenditures?', md)
        self.assertIn('Johansson, J. K. (2006). Global marketing (4th edition ed.). New York: McGraw Hill Irwin.', md)

    def test_extract_main_html_with_double_dollar(self):
        """测试html文本中只包含$$的情况不会被误识别为数学公式."""
        html_content = open(os.path.join(self.base_path, 'assets', 'double_dollar.html'), 'r').read()
        md = extract_content_from_main_html(self.url, html_content)
        self.assertIn(r'he present value Hamiltonian is $$\mathcal{H}=e^{-\triangle} U\left( c\right) +\lambda _{1}^{}\left[ f(k)-c\right] +\lambda _{2}\left[ \rho +h(k)\right] $$ and so $$\frac {d\mathcal{H}}{dt} = -\dot \...', md)

    def test_extract_main_html_with_triple_dollar(self):
        """测试html文本中只包含$$$的情况不会被误识别为数学公式."""
        html_content = open(os.path.join(self.base_path, 'assets', 'triple_dollar.html'), 'r').read()
        md = extract_content_from_main_html(self.url, html_content)
        self.assertIn(r'[$$$] Construction Estimator - Multi-Family - Blueprint Staffing, LLC December 07, 2023 at 05:59:10', md)

    def test_extract_main_html_with_mathjax(self):
        """测试包含MathJax数学公式的HTML内容提取."""

        main_html = r'''
        <html><body>
        <div class="options-div-0-0 option-box__items" style="display: none;">
            <span class="bedroom-rate__title">Room Only Rate</span>
            <span class="bedroom-rate__price">£1,230.00</span>
        </div>
        <p cc-select="true" class="mark-selected" data-anno-uid="anno-uid-wygjielbjln" style="">Are the filtrations after these steps. Why only these? Looking at $\mathcal{F}_1$, we can obtain probabilities for the following events:</p>
        <p>正常内容</p>
        </body></html>
        '''

        md = extract_content_from_main_html(self.url, main_html)

        # 验证MathJax数学公式被正确提取
        self.assertIn('$\\mathcal{F}_1$', md)
        self.assertIn('Are the filtrations after these steps', md)
        self.assertIn('正常内容', md)

        # 验证隐藏内容被过滤掉了
        self.assertNotIn('Room Only Rate', md)
        self.assertNotIn('£1,230.00', md)

        # 验证JavaScript代码被过滤掉了
        self.assertNotIn('MathJax=', md)
        self.assertNotIn('processEscapes', md)

    def test_extract_main_html_with_table_with_math(self):
        """测试html中包含table且table中包含数学公式的HTML内容提取."""
        main_html = r'''
        <h2>Character values</h2>
        <p>We give the values of \(\chi\) on generators for \(\left(\mathbb{Z}/3332\mathbb{Z}\right)^\times\).</p>
        <table class="ntdata">
        <tbody>
                <tr>
            <td class="dark border-right border-bottom">\(n\)</td>
            <td class="light border-bottom">\(785\)</td>
            <td class="dark border-bottom">\(885\)</td>
            <td class="light border-bottom">\(1667\)</td>    </tr>
            <tr>
            <td class="dark border-right">\(\chi(n)\)</td>
            <td class="light">\(e\left(\frac{3}{4}\right)\)</td>
            <td class="dark">\(e\left(\frac{2}{3}\right)\)</td>
            <td class="light">\(-1\)</td>    </tr>
        </tbody>
        </table>

        <a name="coefficient_data"></a>
        <h2>Coefficient data</h2>

        <p>For each \(n\) we display the coefficients of the \(q\)-expansion \(a_n\), the
        <a title="Satake parameters [cmf.satake_parameters]" knowl="cmf.satake_parameters" kwargs="">Satake parameters</a> \(\alpha_p\),
        and the Satake angles \(\theta_p = \textrm{Arg}(\alpha_p)\).</p>
        '''

        md = extract_content_from_main_html(self.url, main_html)

        # 验证MathJax数学公式被正确提取
        self.assertIn('We give the values of $\\chi$ on generators for $\\left(\\mathbb{Z}/3332\\mathbb{Z}\\right)^\\times$ ', md)
        self.assertIn('| $n$ | $785$ | $885$ | $1667$ |', md)
        self.assertIn('| $\\chi(n)$ | $e\\left(\\frac{3}{4}\\right)$ | $e\\left(\\frac{2}{3}\\right)$ | $-1$ |', md)

    def test_extract_main_html_with_math_img_width_various_formats(self):
        """测试img标签width属性各种格式的情况，验证不会抛出异常."""
        main_html = r'''
        <p>Some text with inline formula:</p>
        <!-- 带单位 px -->
        <img src="https://latex.codecogs.com/gif.latex?E=mc^2" alt="$E=mc^2$" width="50px" height="20px" />
        <p>And a larger image:</p>
        <!-- 带单位 px，超过100 -->
        <img src="https://example.com/large.png" alt="large image" width="200px" />
        <p>Image with percent width:</p>
        <!-- 百分比 -->
        <img src="https://latex.codecogs.com/gif.latex?a^2+b^2=c^2" alt="$a^2+b^2=c^2$" width="80%" />
        <p>Image with float width:</p>
        <!-- 浮点数 -->
        <img src="https://latex.codecogs.com/gif.latex?x^n" alt="$x^n$" width="512.123" />
        <p>Image with float width and unit:</p>
        <!-- 浮点数带单位 -->
        <img src="https://latex.codecogs.com/gif.latex?y^m" alt="$y^m$" width="123.456px" />
        <p>Image with auto width:</p>
        <!-- auto 值 -->
        <img src="https://latex.codecogs.com/gif.latex?z^k" alt="$z^k$" width="auto" />
        <p>Image with em unit:</p>
        <!-- em 单位 -->
        <img src="https://latex.codecogs.com/gif.latex?w^j" alt="$w^j$" width="10em" />
        <p>Image with empty width:</p>
        <!-- 空值 -->
        <img src="https://latex.codecogs.com/gif.latex?v^i" alt="$v^i$" width="" />
        '''

        # 这个测试主要验证不会因为各种 width 值而抛出异常
        md = extract_content_from_main_html(self.url, main_html)
        print(md)

        # 验证文本内容存在
        self.assertIn('Some text with inline formula', md)
        self.assertIn('Image with float width', md)
        self.assertIn('Image with auto width', md)

        # 验证 img 中的数学公式被正确提取
        # width <= 100 的是行内公式 $...$
        self.assertIn('$E=mc^2$', md)  # width="50px", 50 <= 100
        self.assertIn('$a^2+b^2=c^2$', md)  # width="80%", 80 <= 100
        self.assertIn('$z^k$', md)  # width="auto", 无数字
        self.assertIn('$w^j$', md)  # width="10em", 10 <= 100
        self.assertIn('$v^i$', md)  # width="", 空值

        # width > 100 的是行间公式 $$...$$ (多行格式)
        self.assertIn('$$\nx^n\n$$', md)  # width="512.123", 512 > 100
        self.assertIn('$$\ny^m\n$$', md)  # width="123.456px", 123 > 100

    def test_extract_magic_html_with_mathjax(self):
        """测试包含MathJax数学公式的HTML内容提取."""
        raw_html = r'''
        <html>
        <meta charset="utf-8"><meta content="IE=edge" http-equiv="X-UA-Compatible"><meta content="width=device-width,initial-scale=1,shrink-to-fit=no" name="viewport">
        <script>MathJax={tex:{inlineMath:[["$","$"],["\\(","\\)"]],processEscapes:!0},svg:{fontCache:"global"}}</script><script async="" id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-svg.js" type="text/javascript"></script>
        <body>
        <div class="options-div-0-0 option-box__items" style="display: none;">
            <span class="bedroom-rate__title">Room Only Rate</span>
            <span class="bedroom-rate__price">£1,230.00</span>
        </div>
        <p cc-select="true" class="mark-selected" data-anno-uid="anno-uid-wygjielbjln" style="">Are the filtrations after these steps. Why only these? Looking at $\mathcal{F}_1$, we can obtain probabilities for the following events:</p>
        <p>正常内容</p>
        </body></html>
        '''

        md = extract_content_from_html_with_magic_html(self.url, raw_html)

        # 验证MathJax数学公式被正确提取
        self.assertIn('$\\mathcal{F}_1$', md)
        self.assertIn('Are the filtrations after these steps', md)
        self.assertIn('正常内容', md)

        # 验证隐藏内容被过滤掉了
        self.assertNotIn('Room Only Rate', md)
        self.assertNotIn('£1,230.00', md)

        # 验证JavaScript代码被过滤掉了
        self.assertNotIn('MathJax=', md)
        self.assertNotIn('processEscapes', md)


if __name__ == '__main__':
    unittest.main(verbosity=2)
    TestSimple().test_extract_main_html_with_math_img_width_various_formats()
