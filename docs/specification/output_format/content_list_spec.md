# 流水线content_list格式数据输出标准
## https://aicarrier.feishu.cn/wiki/RWZywKLW8iSvn6kZWGBc70JSn6f
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
```

使用数组而非类似`page_index=1` 的方式组织是为了能够快速索引到某一页的数据。
对于网页大多数情况下只有一页。

<b>支持的文档元素类型</b>

| ----               | 网页 | 文档 | 子类型 |说明                                                                                 |
| ------------------ | ---- | ---- | -------------- |------------------------------------------------------------------------------------ |
| code               | ✅   | ✅   | - |代码                                                                                 |
| algorithm          | ❌   | ✅   | - |伪代码                                                                               |
| equation-interline | ✅   | ✅   | - |行内公式                                                                             |
| image              | ✅   | ✅   | `general`, `chart` |图片                                                                                 |
| table              | ✅   | ✅   | `simple_table`, `complex_table` |simple table可转化为markdown的表格 ,否则是complex_table               |
| list               | ✅   | ✅   | `text_list`, `reference_list` | text_list是普通的列表，reference_list是论文里的参考文献列表      |
| title              | ✅   | ✅   |      |标题                                                                                 |
| paragraph          | ✅   | ✅   |      |文字可表示可打印内容，由`text_content`所表示 |
| page_header        | ❌   | ✅   |      |文档页眉                                                                             |
| page_footer        | ❌   | ✅   |      |文档页脚                                                                             |
| page_number        | ❌   | ✅   |      |文档页码                                                                             |
| page_aside_text    | ❌   | ✅   |      |文档边注                                                                             |
| page_footnote      | ❌   | ✅   |      |文档论文脚注                                                                         |

其中可打印文本均使用`text_content`结构表示（例如拼音，普通纯文本，行内公式，行内代码，markdown文本)：

```json
{
  "type": "text|equation_inline|code_inline|md|phonetic",
  "content": "printable string"
}

```
其中type可以取值为：
- `text` : 普通文字
- `equation_inline` : 行内公式，例如`爱因斯坦的智能方程公式E=MC^2是个伟大的发现。`
- `code_inline`: 行内代码，例如`执行ls命令查看目录下的文件`
- `md`： markdown格式的文本
- `phonetic`: 汉语拼音

**如有必要刻意继续扩展**

## 字段定义

### 代码段(code)

代表多行的独立代码段

- 在PDF里伪代码被分入 `algorithm`类
- 在网页里则不区分可运行代码和伪代码，但是有`行内代码`，行内代码位于`paragraph`

```json
{
  "type": "code",
  "bbox":[x1, y1, x2, y2]
  "content": {
    "code_caption":[text_content_1, text_content_2],
    "code_content": "def add(a, b):\\n return a + b",
    "language":"python",
    "by": "tag_code"
  }
}
```

| 字段                 | 类型                  | 描述                                                                 | 是否必须(文档) |是否必须(网页)  |
| -------------------- | -------------------- | -------------------------------------------------------------------- | ------------- | ------------------ |
| type                 | string               | 值固定为code                                                          | 是            | 是                 |
| content.code_content | string               | 干净的，格式化过的代码内容                                              | 是            | 是                 |
| content.code_caption | list[text_content]   | 代码标题，可以有多个。网页没有此字段, 每一个元素是一个`text_content`结构  | 否             | 无                 |
| content.language     | string               | 代码语言，python\\cpp\\php...                                         | 可选           | 可选               |
| content.by           | string               | 哪种代码高亮工具 、自定义规则,目前只在网页里有                           | 可选           | 可选               |

### 伪代码(algorithm)

> ⚠️只在文档中出现，网页中无

```json
{
  "type":"algorithm",
  "bbox": [x1, y1, x2, y2],
  "content":{
    "algorithm_content":"循环:\n当x<0时停止",
    "algorithm_caption":[text_content_1, text_content_2]
  }
}

```

| 字段                      | 类型   | 描述                                                           | 是否必须(文档)          | 是否必须(网页) |
| ------------------------- | -------------------- | ------------------------------------------------------------- | ---------------------- | ------------- |
| type                      | string               | 固定为algorithm，代表伪代码内容                                 | 是                     |  无           |
| content.algorithm_content | string               | 干净的，格式化过的代码内容                                       | 是                    | 无            |
| content.algorithm_caption | list[text_content]   | 代码标题，可以有多个。网页没有此字段。每个元素是`text_content`结构 | 可选                   | 无            |

### 行间公式段(equation_interline)

```json
{
  "type": "equation_interline",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "math_content": "a^2 + b^2 = c^2",
    "math_type": "latex",
    "by": "mathjax_mock"
  }
}
```

| 字段                 | 类型   | 描述                                                                  | 是否必须(文档) |是否必须(网页) |
| -------------------- | ------ | -------------------------------------------------------------------- | ------------- |------------- |
| type                 | string | 可选为equation-interline或者equation-inline                           | 是            | 是           |
| content.math_content | string | 干净的，格式化过的公式内容。无论是行内还是行间公式两边都不能有$            | 是            | 是           |
| content.math_type    | string | 公式语言类型，latex\\mathml\\asciimath                                 | 无           | 是            |
| content.by           | string | 原html中使用公式渲染器，mathjax\\katex                                  | 无           | 是            |
| content.image_source | dict   | {"url":"http://xxx.com/1.png", "path":"/mnt/data/1.png", "base64":""} | 需要有        | 无           |

### 图片段(image)

```json
{
  "type": "image",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "image_type":"general | chat",
    "image_source": {"url":"http://xxx.com/1.png", "path":"/mnt/data/1.png", "base64":""},
    "image_caption": [text_content_1, text_content_2],
    "image_footnote":[text_content_1, text_content_2],
    "alt": text_content,
    "title": text_content
  }
}
```

| 字段             | 类型                     | 描述                                                                                        | 是否必须(文档)              |是否必须(网页)        |
| ---------------- | ------                  | ------------------------------------------------------------------------------------------- | -------------------------- | ------------------- |
| type                  | string             | 值固定为`image`                                                                              | 是                         | 是                  |
| content.image_type    | string             | 可选值为`general`普通图片，`chat` 图表（柱状图，折线图等）                                      | 是                         | 固定为`general`      |
| content.image_source  | dict               | key有`url`代表网络图片地址, `path`代表本地存储如磁盘，s3, ftp等, `base64` 代表以base64编码的图片 | 支持`path`,`base64`         | 支持`url`,`base64`  |
| content.image_caption | list[text_content] | 图片的caption属性                                                                            | 可以有多个                  | 只有1个元素          |
| content.image_footnote| list[text_content] | 图片的footnote属性                                                                           | 可以有多个                  | 没有                 |
| content.alt           | `text_content`     | 网页图片的alt属性                                                                             | 没有                       | 只有一个             |
| content.title         | `text_content`     | 网页图片的title属性                                                                           | 没有                       | 只有一个             |

> 对于网页来说image_source里`url`和`base64`二者必须有一个，数据使用优先级是`base64`>`url`。


### 表格[含跨行、列合并，嵌套表格]

```json
{
  "type": "complex_table",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "html": "<table><tbody><tr><th rowspan=\"2\">指标</th><th colspan=\"2\">数据</th></tr><tr><td>2023</td><td>2024</td></tr><tr><td>营收</td><td>10</td><td>15</td></tr></tbody></table>",
    "table_type":"comlex_table | simple_table" # 复杂表 | 简单表
    "table_nest_level": 1,
    "table_caption":[text_content_1, text_content_2],
    "table_footnote":[text_content_1, text_content_2],
    "image_source":{"url":"", "path":"", "base64":""}
  }
}
```

| 字段                     | 类型   | 描述                                          | 是否必须 |
| ------------------------ | ------ | --------------------------------------------- | -------- |
| type                     | string | 可选值为simple_table、complex_table           | 是       |
| bbox                     | 四元组 | 元素位置坐标                                  | 可选     |
| content.html             | string | 表格的html内容                                | 是       |
| content.table_type       | string | 取值为`complex_table`或者`simple_table`       | 是       |
| content.table_nest_level | int    | table嵌套层级(单个table为1,两层为2，以此类推) | 可选     |
| content.table_caption    | list   | 表格的caption内容                             | 否       |
| content.table_footnote   | list   | 表格的footnote内容                            | 否       |

> **complex_table** 是有单元格合并的表，不能转为markdown；**simple_table** 是没有单元格合并的表格，可以用markdown表达

### 列表段\[支持嵌套\]

```json
{
  "type": "list",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "list_type": "text_list | reference_list" ,// 普通list 或者是论文里的引文列表(html里没有)
    "attribute": "definition",
    "list_nest_level": 1,
    "list_items":[
      {
        "item_type":"text", // 此处是text的例子，如果是list类型，那么item_content就是一个新的list
        "item_content": text_content
      },
      {
        "item_type": "list", // 嵌套的列表,此时item_content是一个新的list
        "item_content": {
            "type": "list",
            "bbox":[a,b,c,d],
            "content": {
                "list_type": "text_list",
                "attribute":"definition",
                "list_nest_level": 2,
                "list_items":[]
            }
          }//end item_content
      }
    ]
  }
}
```

| 字段                    | 类型   | 描述                                                      | 是否必须 |
| ----------------------- | ------ | --------------------------------------------------------- | -------- |
| type                    | string | 值固定为list                                              | 是       |
| bbox                    | 四元组 | 元素位置坐标                                              | 可选     |
| content.items           | array  | 列表项，每个元素是N个段落，段落里的元素是文本、公式或代码 | 是       |
| content.attribute  | string | unordered/ordered/definition                              | 可选     |
| content.list_nest_level | int    | list的嵌套层级(单层list list_nest_level为1)               | 可选     |

<b>items字段说明</b>

- `items`是一个二维数组，每个元素是一个段落，段落里的元素是文本、公式、markdown或行内代码。
- 每个元素是一个对象，包含字段：c和t。 c是内容content首字母，t是类型type首字母。
- t的取值同`paragraph`


### 标题段

```json
{
  "type": "title",
  "bbox": [x1, y1, x2, y2],
  "content": {
    "title_content": text_content,
    "level": 1
  }
}
```

| 字段                  | 类型   | 描述                 | 是否必须 |
| --------------------- | ------ | -------------------- | -------- |
| type                  | string | 值固定为title        | 是       |
| bbox                  | 四元组 | 元素位置坐标         | 可选     |
| content.title_content | text_content | 标题内容             | 是       |
| content.level         | int    | 标题级别，1-N, 1最大 | 可选     |

### 段落

```json
{
  "type": "paragraph",
  "bbox": [x1, y1, x2, y2],
  "content": [
     text_content_1, # 代表一句纯文本
     text_content_2, # 行内公式
     text_content_3, # 纯文本
     text_content_4, # 行内代码
     text_content_5, # 拼音
  ]
}
```

| 字段    | 类型   | 描述                                                            | 是否必须 |
| ------- | ------ | --------------------------------------------------------------- | -------- |
| type    | string | 值固定为paragraph                                               | 是       |
| bbox    | 四元组 | 元素位置坐标                                                    | 可选     |
| content | list[text_content]  | 段落内容，每个元素是一个对象，包含字段c和t。 c是内容，t是类型。 | 是       |

<b>content字段说明</b>

- content是一个数组，每个元素是一个对象，包含字段：`c`和`t`。 c是内容，t是类型。
- `t`的取值有以下几种：
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
    "page_header_content": text_content,
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
    "page_footer_content": text_content,
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
    "page_number_content": text_content,
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
    "page_aside_text_content": text_content,
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
    "page_footnote_content": text_content,
  }
}
```



