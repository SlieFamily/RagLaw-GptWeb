# CrimeKgAssitant说明及修复日志

## 原 `README`

> 🔔[原项目内容介绍](RAW_README.md)

## 依赖包 & es服务

### Python 库

- `elasticsearch`
- `jieba`

### 服务器

此外，为了连接服务器，还需要在本地搭建 Elasticsearch 的服务器（官网下载）。

启动服务后还会报错，这是因为最新版本默认启动了**安全模式**，需要去配置文件（`/config/elasticsearch.yml`）下修改：

```yaml
xpack.security.enabled: false
```

### IK Analyzer插件

IK Analyzer插件 用以提供智能分词，是 elasticsearch 的插件之一，也需要手动安装(`x.x.x`为版本号)：

```shell
bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-ik/x.x.x
```

## 下载词嵌入字典

运行 `crime_qa.py` 需要已经训练好的**词嵌入**(`embedding/word_vec_300.bin`)，作者给出了下载地址。

> 链接:https://pan.baidu.com/s/1onNkHJBZH5GRYBC28uYx9Q 密码:44lp

## 部署QA系统

本项目的QA实现较为简单。一句话概括就是：

事先训练一个 word2vec 模型(`vector_train.py`)，将数据集中的question根据 word2vec 模型做embedding(`build_qa_database.py` )，在问答时，将当前question也生成embedding，然后在elasticsearch数据库中找到与之匹配的原question，从而根据原question的answer进行回复(`crime_qa.py`)。

所以要实现本项目的QA系统，仅需以下几个步骤：

1. 保证 es服务器 正在运行；
2. 运行`train_vector.py`训练得到一个 word2vec 模型，或者直接下载：`embedding/word_vec_300.bin`；
3. 运行 `build_qa_database.py` 在本地 es服务器 中生成数据；
4. 此后仅需运行 `crime_qa.py` ，在控制台实现QA。

## 附：修复es7.x+的不兼容

### 创建对象实例

```python
# Elasticsearch([{"host": "127.0.0.1", "port": 9200}]) 
Elasticsearch([{"host": "127.0.0.1", "port": 9200, 'scheme': 'http'}]) # 需要指定协议
```

### search 方法

es7.x 版本以后不需要指定 `doc_type` 和 `size`，但是`size`要整合到`body`里：

```python
# es.search(index=self._index, doc_type=self.doc_type, body=query_body, size=20)
es.search(index=self._index, body=query_body)
```

其中，`body` 如下：

```python
query_body = {
        "query": {
            "match": {
                key: value,
            }
        },
        "size": 20, # es7.x 版本以后size要整合到body里
}
```

### create 方法

和上面类似，create中的`mapping`不能含有 `doc_type` ：

```python
node_mappings = {
    "mappings": {
        # self.doc_type: {    # es7.x 版本以后不需要doc_type
        "properties": {
            "question": {    # field: 问题
                "type": "text",    # lxw NOTE: cannot be string
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
                "index": "true"    # The index option controls whether field values are indexed.
            },
            "answers": {  # field: 问题
                "type": "text",  # lxw NOTE: cannot be string
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
                "index": "true"  # The index option controls whether field values are indexed.
            },
        }
        # }
    }
}

es.indices.create(index=self._index, body=node_mappings)
```

### bulk 函数

es 7.x版本之后，`_type`的概念被移除，以支持单索引类型（single-document-type-per-index）。所以向Elasticsearch发送请求并包含的`_type`参数应该删掉，仅使用索引名和文档ID来操作文档。

```python
action = {
    "_index": pie._index,
    # "_type": pie.doc_type, #es7.x 之后没有 _type 了
    "_source": {
        "question": item['question'],
        "answers": '\n'.join(item['answers']),
    }
}
```

