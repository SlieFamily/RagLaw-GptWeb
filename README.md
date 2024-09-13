# 基于 RAG+GPT+Flask 的法律知识问答 Web系统

> **项目支持**：
>
> - Web Page -> [💬petals-infra/chat.petals.dev](https://github.com/petals-infra/chat.petals.dev)
> - Dataset -> 

## 界面预览

![](static/demo.png)

## 快速开始

1. `git clone` 或下载本项目（`raw_repo` 不必需）

2. 安装相关依赖库（懒人可直接 `pip install -r requirements.txt`）

3. 下载 `qa_with_ref_92k.json` 数据集至 `data` 目录

4. 启动 **Elasticsearch 服务端**程序（比如 Windows 系统是启动 `elasticsearch\bin\elasticsearch.bat`）

5. 运行 `python data_structures.py` 将数据集 embedding 到数据库（此过程耗时较久）

6. 启动 Web app。在项目根目录运行：
    ```shell
    flask run --host=0.0.0.0 --port=5000
    ```

## 技术细节

### RAG



### API

本项目使用 websocket 实现请求 `/api/v2/generate`

