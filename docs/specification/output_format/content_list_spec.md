# 流水线content_list格式数据输出标准

## 目的

定义content_list的目的是为了统一流水线输出的数据格式，无论是网页、电子书、富文本pdf,word，ppt等，都可以转化到这个格式。
使得不同的下游任务可以快速根据content_list导出所需要的数据格式。

> 目的不是用户最终使用的格式，而是为了快速转化为下游任务需要的格式，例如大语言模型不需要图和音视频而多模态模型需要用。

## 样例

<b>遵循原则</b>

- content_list 是被分解的文档，每个元素是文章中的一段内容，可以使文本、图片、代码、音视频等。
- 每个元素的表达方式是不一样的，受制于其`type`类型，逐层深入。
- 为了调试找问题方便，留下了`raw_content`字段，用于存储原始的文本内容。
- 整体结构是一个二维数组，每个元素是一个数组，表示一页内容。如果页面为空，则需要填充一个空数组进行占位，默认二维数组下标即为**页码**。

```json
[
  [
    {
      "type": "code",
      "raw_content": "<code>def add(a, b):\\n    return a + b</code>",
      "inline": false,
      "content": {
        "code_content": "def add(a, b):\\n return a + b",
        "by": "tag_code"
      }
    },
    {
      "type": "equation-interline",
      "raw_content": "<p>$$a^2 + b^2 = c^2$$</p>",
      "content": {
        "math_content": "a^2 + b^2 = c^2",
        "math_type": "latex",
        "by": "mathjax_mock"
      }
    },
    {
      "type": "image",
      "raw_content": "<figure class=\"thumb tright thumbinner\" style=\"width:182px;\"><a href=\"http://static4.wikia.nocookie.net/__cb20120619225143/central/images/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png\" class=\"image\"><img alt=\"Screen Shot 2012-06-19 at 6.25.45 PM\" src=\"data:image/gif;base64,R0lGODlhAQABAIABAAAAAP///yH5BAEAAAEALAAAAAABAAEAQAICTAEAOw%3D%3D\" width=\"180\" height=\"113\" class=\"thumbimage lzy lzyPlcHld\" data-image-name=\"Screen Shot 2012-06-19 at 6.25.45 PM.png\" data-image-key=\"Screen_Shot_2012-06-19_at_6.25.45_PM.png\" data-src=\"http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png\" onload='if(typeof ImgLzy==\"object\"){ImgLzy.load(this)}'><noscript><img alt=\"Screen Shot 2012-06-19 at 6.25.45 PM\" src=\"http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png\" width=\"180\" height=\"113\" class=\"thumbimage\" data-image-name=\"Screen Shot 2012-06-19 at 6.25.45 PM.png\" data-image-key=\"Screen_Shot_2012-06-19_at_6.25.45_PM.png\"></noscript></a><a href=\"/wiki/File:Screen_Shot_2012-06-19_at_6.25.45_PM.png\" class=\"internal sprite details magnify\" title=\"View photo details\"></a><figcaption class=\"thumbcaption\">What it ACTUALLY looks like</figcaption></figure>",
      "content": {
        "url": "http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png",
        "data": null,
        "alt": "Screen Shot 2012-06-19 at 6.25.45 PM",
        "title": null,
        "caption": "What it ACTUALLY looks like"
      }
    },
    {
      "type": "simple_table",
      "raw_content": "<table><tr><th>项目</th><th>值</th></tr><tr><td>A</td><td>1</td></tr></table>",
      "content": {
        "html": "<table><tr><th>项目</th><th>值</th></tr><tr><td>A</td><td>1</td></tr></table>",
        "is_complex": false,
        "table_nest_level": 1
      }
    },
    {
      "type": "complex_table",
      "raw_content": "<table><tbody><tr><th rowspan=\"2\">指标</th><th colspan=\"2\">数据</th></tr><tr><td>2023</td><td>2024</td></tr><tr><td>营收</td><td>10</td><td>15</td></tr></tbody></table>",
      "content": {
        "html": "<table><tbody><tr><th rowspan=\"2\">指标</th><th colspan=\"2\">数据</th></tr><tr><td>2023</td><td>2024</td></tr><tr><td>营收</td><td>10</td><td>15</td></tr></tbody></table>",
        "is_complex": true,
        "table_nest_level": "1"
      }
    },
    {
      "type": "list",
      "raw_content": "<dl><dt>外层列表项</dt><dd><ol><li>行内公式: <ccmath-inline type=\"latex\" by=\"mathjax_mock\" html=\"$E=mc^2$\">E=mc^2</ccmath-inline></li><li>行内代码: <cccode-inline by=\"tag_code\" html=\"&lt;code&gt;x = 1&lt;/code&gt;\" inline=\"true\">x = 1</cccode-inline></li></ol></dd><dt>外层另一个列表项</dt><dd><menu><li>第二层菜单项</li></menu></dd></dl>",
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
    },
    {
      "type": "title",
      "raw_content": "<h1>大模型好，大模型棒1</h1>",
      "content": {
        "title_content": "大模型好，大模型棒1",
        "level": "1"
      }
    },
    {
      "type": "paragraph",
      "raw_content": "<html><head><title>Who Is In Your Top 3 Mentalists Of All Time? &lt;code&gt;x = 1&lt;/code&gt; <ccmath-inline type=\"latex\" by=\"mathjax_mock\" html=\"$E=mc^2$\">E=mc^2</ccmath-inline> • MAGICIANSANDMAGIC.COM</title></head></html>",
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
  ],
  []
]
```

## 字段定义

### 代码段

```json
{
  "type": "code",
  "raw_content": "<code>def add(a, b):\\n    return a + b</code>",
  "inline": false,
  "content": {
    "code_content": "def add(a, b):\\n return a + b",
    "by": "tag_code"
  }
}
```

| 字段                 | 类型   | 描述                          | 是否必须 |
| -------------------- | ------ | ----------------------------- | -------- |
| type                 | string | 值固定为code                  | 是       |
| raw_content          | string | 原始文本内容                  | 可选     |
| inline               | bool   | 是否为行内代码                | 是       |
| content.code_content | string | 干净的，格式化过的代码内容    | 是       |
| content.language     | string | 代码语言，python\\cpp\\php... | 可选     |
| content.by           | string | 哪种代码高亮工具 、自定义规则 | 是       |

### 公式段

```json
{
  "type": "equation-interline",
  "raw_content": "<p>$$a^2 + b^2 = c^2$$</p>",
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
| raw_content          | string | 原始文本内容                                                    | 可选     |
| content.math_content | string | 干净的，格式化过的公式内容。无论是行内还是行间公式两边都不能有$ | 是       |
| content.math_type    | string | 公式语言类型，latex\\mathml\\asciimath                          | 可选     |
| content.by           | string | 原html中使用公式渲染器，mathjax\\katex                          | 可选     |

### 图片段

```json
{
  "type": "image",
  "raw_content": "<figure class=\"thumb tright thumbinner\" style=\"width:182px;\"><a href=\"http://static4.wikia.nocookie.net/__cb20120619225143/central/images/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png\" class=\"image\"><img alt=\"Screen Shot 2012-06-19 at 6.25.45 PM\" src=\"data:image/gif;base64,R0lGODlhAQABAIABAAAAAP///yH5BAEAAAEALAAAAAABAAEAQAICTAEAOw%3D%3D\" width=\"180\" height=\"113\" class=\"thumbimage lzy lzyPlcHld\" data-image-name=\"Screen Shot 2012-06-19 at 6.25.45 PM.png\" data-image-key=\"Screen_Shot_2012-06-19_at_6.25.45_PM.png\" data-src=\"http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png\" onload='if(typeof ImgLzy==\"object\"){ImgLzy.load(this)}'><noscript><img alt=\"Screen Shot 2012-06-19 at 6.25.45 PM\" src=\"http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png\" width=\"180\" height=\"113\" class=\"thumbimage\" data-image-name=\"Screen Shot 2012-06-19 at 6.25.45 PM.png\" data-image-key=\"Screen_Shot_2012-06-19_at_6.25.45_PM.png\"></noscript></a><a href=\"/wiki/File:Screen_Shot_2012-06-19_at_6.25.45_PM.png\" class=\"internal sprite details magnify\" title=\"View photo details\"></a><figcaption class=\"thumbcaption\">What it ACTUALLY looks like</figcaption></figure>",
  "content": {
    "url": "http://static4.wikia.nocookie.net/__cb20120619225143/central/images/thumb/3/30/Screen_Shot_2012-06-19_at_6.25.45_PM.png/180px-Screen_Shot_2012-06-19_at_6.25.45_PM.png",
    "data": null,
    "alt": "Screen Shot 2012-06-19 at 6.25.45 PM",
    "title": null,
    "caption": "What it ACTUALLY looks like"
  }
}
```

| 字段            | 类型   | 描述                 | 是否必须 |
| --------------- | ------ | -------------------- | -------- |
| type            | string | 值固定为image        | 是       |
| raw_content     | string | 原始文本内容         | 可选     |
| content.url     | string | 图片的url地址        | 可选     |
| content.data    | string | base64形式的图片数据 | 可选     |
| content.alt     | string | 图片的alt属性        | 可选     |
| content.title   | string | 图片的title属性      | 可选     |
| content.caption | string | 图片的caption属性    | 可选     |

> `content.url`和`content.data`二者必须有一个，数据使用优先级是`data`>`url`。

### 音频段(未实现)

```json
{
    "type": "audio",
    "raw_content": null,
    "content": {
        "sources": ["https://www.example.com/audio.mp3"],
        "path": "s3://llm-media/audio.mp3",
        "title": "example audio",
        "caption": "text from somewhere"
    }
}
```

| 字段            | 类型   | 描述               | 是否必须 |
| --------------- | ------ | ------------------ | -------- |
| type            | string | 值固定为audio      | 是       |
| bbox            | array  | \[x1, y1, x2, y2\] | 可选     |
| raw_content     | string | 原始文本内容       | 可选     |
| content.sources | array  | 音频的url地址      | 可选     |
| content.path    | string | 音频的存储路径     | 可选     |
| content.title   | string | 音频的title属性    | 可选     |
| content.caption | string | 音频的caption属性  | 可选     |

### 视频段(未实现)

```json
{
        "type": "video",
        "bbox": [0, 0, 50, 50],
        "raw_content": null,
        "content": {
            "sources": ["https://www.example.com/video.avi"],
            "path": "s3://llm-media/video.mp4",
            "title": "example video",
            "caption": "text from somewhere"
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
| content.caption | string | 视频的caption属性  | 可选     |

### 表格段

```json
{
  "type": "complex_table",
  "raw_content": "<table><tbody><tr><th rowspan=\"2\">指标</th><th colspan=\"2\">数据</th></tr><tr><td>2023</td><td>2024</td></tr><tr><td>营收</td><td>10</td><td>15</td></tr></tbody></table>",
  "content": {
    "html": "<table><tbody><tr><th rowspan=\"2\">指标</th><th colspan=\"2\">数据</th></tr><tr><td>2023</td><td>2024</td></tr><tr><td>营收</td><td>10</td><td>15</td></tr></tbody></table>",
    "is_complex": true,
    "table_nest_level": "1"
  }
}
```

| 字段                     | 类型    | 描述                                              | 是否必须 |
| ------------------------ | ------- | ------------------------------------------------- | -------- |
| type                     | string  | 可选值为simple_table、complex_table               | 是       |
| raw_content              | string  | 原始文本内容                                      | 可选     |
| content.html             | string  | 表格的html内容                                    | 是       |
| content.is_complex       | boolean | 是否是复杂表格(跨行、跨列的/嵌套表格, 默认为false | 可选     |
| content.table_nest_level | int     | table嵌套层级(单个table为1,两层为2，以此类推)     | 可选     |

### 列表段

```json
{
  "type": "list",
  "raw_content": "<dl><dt>外层列表项</dt><dd><ol><li>行内公式: <ccmath-inline type=\"latex\" by=\"mathjax_mock\" html=\"$E=mc^2$\">E=mc^2</ccmath-inline></li><li>行内代码: <cccode-inline by=\"tag_code\" html=\"&lt;code&gt;x = 1&lt;/code&gt;\" inline=\"true\">x = 1</cccode-inline></li></ol></dd><dt>外层另一个列表项</dt><dd><menu><li>第二层菜单项</li></menu></dd></dl>",
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
| raw_content             | string | 原始文本内容                                              | 可选     |
| content.items           | array  | 列表项，每个元素是N个段落，段落里的元素是文本、公式或代码 | 是       |
| content.list_attribute  | string | unordered/ordered/definition                              | 可选     |
| content.list_nest_level | int    | list的嵌套层级(单层list list_nest_level为1)               | 可选     |

<b>items字段说明</b>

- `items`是一个二维数组，每个元素是一个段落，段落里的元素是文本、公式、markdown或行内代码。
- 每个元素是一个对象，包含字段：c和t。 c是内容，t是类型。
- t的取值有4种：`text`、`equation-inline`、`md`、`code-inline`。

### 标题段

```json
{
  "type": "title",
  "raw_content": "<h1>大模型好，大模型棒1</h1>",
  "content": {
    "title_content": "大模型好，大模型棒1",
    "level": "1"
  }
}
```

| 字段                  | 类型   | 描述                 | 是否必须 |
| --------------------- | ------ | -------------------- | -------- |
| type                  | string | 值固定为title        | 是       |
| raw_content           | string | 原始文本内容         | 可选     |
| content.title_content | string | 标题内容             | 是       |
| content.level         | int    | 标题级别，1-N, 1最大 | 可选     |

### 段落

```json
{
  "type": "paragraph",
  "raw_content": "<html><head><title>Who Is In Your Top 3 Mentalists Of All Time? &lt;code&gt;x = 1&lt;/code&gt; <ccmath-inline type=\"latex\" by=\"mathjax_mock\" html=\"$E=mc^2$\">E=mc^2</ccmath-inline> • MAGICIANSANDMAGIC.COM</title></head></html>",
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

| 字段        | 类型   | 描述                                                            | 是否必须 |
| ----------- | ------ | --------------------------------------------------------------- | -------- |
| type        | string | 值固定为paragraph                                               | 是       |
| raw_content | string | 原始文本内容                                                    | 可选     |
| content     | array  | 段落内容，每个元素是一个对象，包含字段c和t。 c是内容，t是类型。 | 是       |

<b>content字段说明</b>

- content是一个数组，每个元素是一个对象，包含字段：`c`和`t`。 c是内容，t是类型。
- t的取值有4种：`text`、`equation-inline`、`md`、`code-inline`。

## 参考

- [图文交错数据标准格式（2.1）](https://aicarrier.feishu.cn/wiki/L1vUwB0Ozi9vZBkdrzycaHwAn0e)
