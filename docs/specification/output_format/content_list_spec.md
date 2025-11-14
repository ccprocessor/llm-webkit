# 流水线content_list格式数据输出标准

## 目的

定义content_list的目的是为了统一流水线输出的数据格式，无论是网页、电子书、富文本pdf,word，ppt等，都可以转化到这个格式。
使得不同的下游任务可以：

1. 快速根据content_list导出所需要的数据格式。
2. 利用content_list筛选包含某些元素的内容

> 目的不是用户最终使用的格式，而是为了快速转化为下游任务需要的格式，例如大语言模型不需要图和音视频而多模态模型需要用。

## 详细说明

<b>遵循原则</b>

- content_list 是被分解的文档，每个元素是文章中的一段内容，可以使文本、图片、代码、音视频等。
- 每个元素的表达方式是不一样的，受制于其`type`类型，逐层深入。
- 整体结构是一个二维数组，第一维表示一页内容。如果页面为空，则需要填充一个**空数组进行占位**，二维数组下标即为**页码**。

<b>整体结构</b>

```json
[ //文档结构开始
  [   //这里是第一页的内容开始，里面每个字典表述一个文档元素的全部信息
     {
      "type":"code",
      "bbox":[x0, y0, x1, y1],
      "content":{
        //content内容根据type不同而不同
      },
      {
        "type":"image",
        "bbox":[x0, y0, x1, y1],
        "content":{
          // ...
        }
      },
      ...
     }
  ],//第一页内容结束
  [
      //这里是第二页的内容，如果没有内容则必须留空（例如某一页PDF是空白)
  ],
] //结构结束

使用数组而非类似`page_index=1` 的方式组织是为了能够快速索引到某一页的数据。
对于网页大多数情况下只有一页。
```

<b>支持的文档元素类型</b>

| ----               | 网页 | 文档 | 说明                                                                                 |
| ------------------ | ---- | ---- | ------------------------------------------------------------------------------------ |
| code               | ✅   | ✅   | 代码                                                                                 |
| algorithm          | ❌   | ✅   | 伪代码                                                                               |
| equation-interline | ✅   | ✅   | 行内公式                                                                             |
| image              | ✅   | ✅   | 图片                                                                                 |
| simple_table       | ✅   | ✅   | 可转化为markdown的表格                                                               |
| complex_table      | ✅   | ✅   | 含有合并单元格的表格，不可转为markdown                                               |
| list               | ✅   | ✅   | 列表                                                                                 |
| ref_list           | ❌   | ✅   | 论文参考文献列表                                                                     |
| title              | ✅   | ✅   | 标题                                                                                 |
| paragraph          | ✅   | ✅   | 文字可表示内容，内部可以含有多种文字类型，`纯文本`，`行内公式`，`行内代码`，`拼音`等 |
| audio              | ✅   | ❌   | 音频，只在网页数据里有                                                               |
| video              | ✅   | ❌   | 视频，只在网页数据里有                                                               |
| page_header        | ❌   | ✅   | 文档页眉                                                                             |
| page_footer        | ❌   | ✅   | 文档页脚                                                                             |
| page_number        | ❌   | ✅   | 文档页码                                                                             |
| page_aside_text    | ❌   | ✅   | 文档边注                                                                             |
| page_footnote      | ❌   | ✅   | 文档论文脚注                                                                         |

其中`paragraph`又由以下几种类型组成：

- `equation-inline`代表行内公式
- `text`代表普通纯文本
- `code-inline`代表行内文本，例如“执行linux`ls`命令”

## 字段定义

### 代码段

代表多行的独立代码段

- 在PDF里伪代码被分入 `algorithm`类
- 在网页里则不区分可运行代码和伪代码，但是有`行内代码`，行内代码位于`paragraph`

```json
{
  "type": "code",
  "bbox":[x1, y1, x2, y2]
  "content": {
    "caption":["下面是一段python求和函数"],
    "code_content": "def add(a, b):\\n return a + b",
    "language":"python",
    "by": "tag_code"
  }
}
```

| 字段                 | 类型   | 描述                                           | 是否必须 |
| -------------------- | ------ | ---------------------------------------------- | -------- |
| type                 | string | 值固定为code                                   | 是       |
| content.code_content | string | 干净的，格式化过的代码内容                     | 是       |
| content.caption      | list   | 代码标题，可以有多个。网页没有此字段           | 否       |
| content.language     | string | 代码语言，python\\cpp\\php...                  | 可选     |
| content.by           | string | 哪种代码高亮工具 、自定义规则,目前只在网页里有 | 可选     |

### 伪代码

> ⚠️只在文档中出现，网页中无

```json
{
  "type":"algorithm",
  "bbox": [x1, y1, x2, y2],
  "content":{
    "algorithm_content":"",
    "caption":["title-1", "title-2",]
  }
}

```

| 字段                      | 类型   | 描述                                 | 是否必须 |
| ------------------------- | ------ | ------------------------------------ | -------- |
| type                      | string | 固定为algorithm，代表伪代码内容      | 是       |
| content.algorithm_content | string | 干净的，格式化过的代码内容           | 是       |
| content.caption           | list   | 代码标题，可以有多个。网页没有此字段 | 否       |

### 行间公式段

```json
{
  "type": "equation-interline",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "math_content": "a^2 + b^2 = c^2",
    "math_type": "latex",
    "by": "mathjax_mock"
  }
}
```

| 字段                 | 类型   | 描述                                                            | 是否必须 |
| -------------------- | ------ | --------------------------------------------------------------- | -------- |
| type                 | string | 可选为equation-interline或者equation-inline                     | 是       |
| content.math_content | string | 干净的，格式化过的公式内容。无论是行内还是行间公式两边都不能有$ | 是       |
| content.math_type    | string | 公式语言类型，latex\\mathml\\asciimath                          | 可选     |
| content.by           | string | 原html中使用公式渲染器，mathjax\\katex                          | 可选     |

### 图片段

```json
{
  "type": "image",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "url": "http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png",
    "data": null,
    "alt": "Screen Shot 2012-06-19 at 6.25.45 PM",
    "title": null,
    "caption": ["What it ACTUALLY looks like"],
    "footnote":[]
  }
}
```

| 字段             | 类型   | 描述                 | 是否必须 |
| ---------------- | ------ | -------------------- | -------- |
| type             | string | 值固定为image        | 是       |
| content.url      | string | 图片的url地址        | 可选     |
| content.data     | string | base64形式的图片数据 | 可选     |
| content.alt      | string | 图片的alt属性        | 可选     |
| content.title    | string | 图片的title属性      | 可选     |
| content.caption  | list   | 图片的caption属性    | 可选     |
| content.footnote | list   | 图片的footnote属性   | 可选     |

> `content.url`和`content.data`二者必须有一个，数据使用优先级是`data`>`url`。

### 音频段

> ⚠️网页中有，文档中没有

```json
{
    "type": "audio",
    "content": {
        "sources": ["https://www.example.com/audio.mp3"],
        "path": "s3://llm-media/audio.mp3",
        "title": "example audio",
        "caption": ["text from somewhere"]
    }
}
```

| 字段            | 类型   | 描述               | 是否必须 |
| --------------- | ------ | ------------------ | -------- |
| type            | string | 值固定为audio      | 是       |
| bbox            | array  | \[x1, y1, x2, y2\] | 可选     |
| content.sources | array  | 音频的url地址      | 可选     |
| content.path    | string | 音频的存储路径     | 可选     |
| content.title   | string | 音频的title属性    | 可选     |
| content.caption | list   | 音频的caption属性  | 可选     |

### 视频段

> ⚠️网页中有，文档中没有

```json
{
        "type": "video",
        "bbox": [0, 0, 50, 50],
        "raw_content": null,
        "content": {
            "sources": ["https://www.example.com/video.avi"],
            "path": "s3://llm-media/video.mp4",
            "title": "example video",
            "caption": ["text from somewhere"]
        }
    }
```

| 字段            | 类型   | 描述               | 是否必须 |
| --------------- | ------ | ------------------ | -------- |
| type            | string | 值固定为video      | 是       |
| bbox            | array  | \[x1, y1, x2, y2\] | 可选     |
| raw_content     | string | 原始文本内容       | 可选     |
| content.sources | array  | 视频的url地址      | 可选     |
| content.path    | string | 视频的存储路径     | 可选     |
| content.title   | string | 视频的title属性    | 可选     |
| content.caption | list   | 视频的caption属性  | 可选     |

### 复杂表格\[含跨行、列合并，嵌套\]

```json
{
  "type": "complex_table",
  "content": {
    "html": "<table><tbody><tr><th rowspan=\"2\">指标</th><th colspan=\"2\">数据</th></tr><tr><td>2023</td><td>2024</td></tr><tr><td>营收</td><td>10</td><td>15</td></tr></tbody></table>",
    "table_nest_level": "1",
    "caption":[],
    "footnote":[]
  }
}
```

| 字段                     | 类型   | 描述                                          | 是否必须 |
| ------------------------ | ------ | --------------------------------------------- | -------- |
| type                     | string | 可选值为simple_table、complex_table           | 是       |
| bbox                     | 四元组 | 元素位置坐标                                  | 可选     |
| content.html             | string | 表格的html内容                                | 是       |
| content.table_nest_level | int    | table嵌套层级(单个table为1,两层为2，以此类推) | 可选     |
| content.caption          | string | 表格的caption内容                             | 否       |
| content.footnote         | string | 表格的footnote内容                            | 否       |

### 简单表格 \[可用markdown表达的表格\]

```json
{
  "type":"simple_table",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "html":"",
    "caption":[],
    "footnote":[]
  }
}
```

| 字段             | 类型   | 描述                                | 是否必须 |
| ---------------- | ------ | ----------------------------------- | -------- |
| type             | string | 可选值为simple_table、complex_table | 是       |
| bbox             | 四元组 | 元素位置坐标                        | 可选     |
| content.html     | string | 表格的html内容                      | 是       |
| content.caption  | list   | 表格的caption内容                   | 否       |
| content.footnote | list   | 表格的footnote内容                  | 否       |

### 列表段\[支持嵌套\]

```json
{
  "type": "list",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "items": [
      {
        "c": "外层列表项"
      },
      {
        "child_list": {
          "list_attribute": "ordered",
          "items": [
            {
              "c": "行内公式: $E=mc^2$"
            },
            {
              "c": "行内代码: `x = 1`"
            }
          ]
        }
      },
      {
        "c": "外层另一个列表项"
      },
      {
        "child_list": {
          "list_attribute": "unordered",
          "items": [
            {
              "c": "第二层菜单项"
            }
          ]
        }
      }
    ],
    "list_attribute": "definition",
    "list_nest_level": "2"
  }
}
```

| 字段                    | 类型   | 描述                                                      | 是否必须 |
| ----------------------- | ------ | --------------------------------------------------------- | -------- |
| type                    | string | 值固定为list                                              | 是       |
| bbox                    | 四元组 | 元素位置坐标                                              | 可选     |
| content.items           | array  | 列表项，每个元素是N个段落，段落里的元素是文本、公式或代码 | 是       |
| content.list_attribute  | string | unordered/ordered/definition                              | 可选     |
| content.list_nest_level | int    | list的嵌套层级(单层list list_nest_level为1)               | 可选     |

<b>items字段说明</b>

- `items`是一个二维数组，每个元素是一个段落，段落里的元素是文本、公式、markdown或行内代码。
- 每个元素是一个对象，包含字段：c和t。 c是内容content首字母，t是类型type首字母。
- t的取值同`paragraph`

### ref_list 参考文献列表

> ⚠️仅在文档论文中有

```json
{
  "type":"ref_list",
  "bbox":[],
  "content":{
    // same as list
  }
}

```

### 标题段

```json
{
  "type": "title",
  "bbox":[],
  "content": {
    "title_content": "大模型好，大模型棒1",
    "level": "1"
  }
}
```

| 字段                  | 类型   | 描述                 | 是否必须 |
| --------------------- | ------ | -------------------- | -------- |
| type                  | string | 值固定为title        | 是       |
| bbox                  | 四元组 | 元素位置坐标         | 可选     |
| content.title_content | string | 标题内容             | 是       |
| content.level         | int    | 标题级别，1-N, 1最大 | 可选     |

### 段落

```json
{
  "type": "paragraph",
  "bbox":[],
  "content": [
    {
      "c": "Who Is In Your Top 3 Mentalists Of All Time? x = 1",
      "t": "text"
    },
    {
      "c": "E=mc^2",
      "t": "equation-inline"
    },
    {
      "c": "• MAGICIANSANDMAGIC.COM",
      "t": "text"
    }
  ]
}
```

| 字段    | 类型   | 描述                                                            | 是否必须 |
| ------- | ------ | --------------------------------------------------------------- | -------- |
| type    | string | 值固定为paragraph                                               | 是       |
| bbox    | 四元组 | 元素位置坐标                                                    | 可选     |
| content | array  | 段落内容，每个元素是一个对象，包含字段c和t。 c是内容，t是类型。 | 是       |

<b>content字段说明</b>

- content是一个数组，每个元素是一个对象，包含字段：`c`和`t`。 c是内容，t是类型。
- t的取值有一下几种：
  - `text` : 普通文本
  - `equation-inline`： 行内公式
  - `md`：markdown格式的文本，通常用于格式化从网上下来的mardown文档
  - `code-inline`：行内公式，例如 “执行linux的`ls`命令查看文件”
  - `phonetic`：拼音

### 页眉

> ⚠️只在文档中出现，网页中没有此项

```json
{
  "type": "page_header",
  "bbox":[x0, y0, x1, y1],
  "content": {
    "page_header_content": "大模型学习资料",
  }
}
```

### 页脚

> ⚠️只在文档中出现，网页中没有此项

```json
{
  "type": "page_footer",
  "bbox":[x0, y0, x1, y1],
  "content": {
    "page_footer_content": "~~内部资料请勿外传~~",
  }
}
```

### 页码

> ⚠️只在文档中出现，网页中没有此项

```json
{
  "type": "page_number",
  "bbox":[x0, y0, x1, y1],
  "content": {
    "page_number_content": "--12--",
  }
}
```

### 边注

> ⚠️只在文档中出现，网页中没有此项

```json
{
  "type": "page_aside_text",
  "bbox":[x0, y0, x1, y1],
  "content": {
    "page_aside_text_content": "LLM大模型学习资料",
  }
}
```

### 论文脚注

> ⚠️只在文档中出现，网页中没有此项

```json
{
  "type": "page_footnote",
  "bbox":[x0, y0, x1, y1],
  "content": {
    "page_footnote_content": "大模型的代表公司有OpenAI、Claude等",
  }
}
```
