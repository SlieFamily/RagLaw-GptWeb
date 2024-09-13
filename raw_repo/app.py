import os
import time

import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
# import pymongo
import numpy as np
from transformers import BertTokenizer, BertModel, BertTokenizerFast
import torch
from openai import OpenAI

# 加载预训练的模型和 tokenizer
model_name = "bert-base-chinese"
tokenizer = BertTokenizerFast.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)



client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="sk-yjZqS0m2AMylEEFXypJXqT8lRpPPBTnjxL61Qy5S12imSJ7j",
    base_url="https://api.chatanywhere.tech/v1"
)

# messages = [
#     {"role": "system", "content": "You are a helpful Chinese law assistant."},
# ]


def encode_texts(texts):
    inputs = tokenizer(" ".join(texts), padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)
    return embeddings.numpy().tolist()


class ProcessIntoES:
    def __init__(self):
        self._index = "crime_data"
        # self.es = Elasticsearch([{"host": "127.0.0.1", "port": 9200}]) 
        self.es = Elasticsearch([{"host": "127.0.0.1", "port": 9200, 'scheme': 'http'}]) # 需要指定协议
        self.doc_type = "crime"
        cur = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.music_file = os.path.join(cur, 'data/qa_with_ref_92k.json') # 'data/qa_corpus.json'

    '''创建ES索引，确定分词类型'''
    def create_mapping(self):
        node_mappings = {
            "mappings": {
                # self.doc_type: {    # es7.x 版本以后不需要指定doc_type
                    "properties": {
                        "question": { "type": "text" },
                        "answer": { "type": "text" },
                        "reference": { "type": "text" },
                        "question_embedding": {"type": "dense_vector", "dims": 768}, # BERT-base-chinese 的嵌入维度是 768
                        "answer_embedding": {"type": "dense_vector", "dims": 768},
                        "reference_embeddings": {"type": "dense_vector", "dims": 768},
                        
                    }
                # }
            }
        }
        if not self.es.indices.exists(index=self._index):
            self.es.indices.create(index=self._index, body=node_mappings)
            print("Create {} mapping successfully.".format(self._index))
        else:
            print("index({}) already exists.".format(self._index))

    '''批量插入数据'''
    def insert_data_bulk(self, action_list):
        success, _ = bulk(self.es, action_list, index=self._index, raise_on_error=True)
        print("Performed {0} actions. _: {1}".format(success, _))


'''初始化ES，将数据插入到ES数据库当中'''
def init_ES():
    pie = ProcessIntoES()
    # 创建ES的index
    pie.create_mapping()
    start_time = time.time()
    index = 0
    count = 640
    action_list = []
    BULK_COUNT = 100  # 每BULK_COUNT个句子一起插入到ES中

    # 原数据集
    # # for line in open(pie.music_file):
    # for line in open(pie.music_file, encoding='utf-8'): #需要指定编码方式
    #     if not line:
    #         continue
    #     item = json.loads(line)
    #     index += 1
    #     action = {
    #         "_index": pie._index,
    #         # "_type": pie.doc_type, #es7.x 之后没有 _type 了
    #         "_source": {
    #             "question": item['question'],
    #             "answers": '\n'.join(item['answers']),
    #         }
    #     }

    # 新数据集
    with open(pie.music_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 编码参考文档和问题
    for doc in data[64000:]:
        doc["question_embedding"] = encode_texts([doc["question"]])[0]
        doc["answer_embedding"] = encode_texts([doc["answer"]])[0]
        doc["reference_embeddings"] = encode_texts(doc["reference"])[0]

        index += 1
        action = {
            "_index": pie._index,
            "_source": doc,
        }

        action_list.append(action)
        if index > BULK_COUNT:
            pie.insert_data_bulk(action_list=action_list)
            index = 0
            count += 1
            print(f'-----embedded {count}00 QA pairs-----')
            action_list = []
            end_time = time.time()
            print("Time Cost:{0}".format(end_time - start_time))
        print(f'processing {index}% for {count}')

def search_similar_documents(question, top_k=5):
    query_vector = encode_texts(question)[0]
    query = {
        "size": top_k,
        "_source": ["question", "answer", "reference"], 
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": """
                        double maxCosineSimilarity = 0;
                        maxCosineSimilarity = Math.max(maxCosineSimilarity, cosineSimilarity(params.query_vector, 'question_embedding'));
                        maxCosineSimilarity = Math.max(maxCosineSimilarity, cosineSimilarity(params.query_vector, 'answer_embedding'));
                        maxCosineSimilarity = Math.max(maxCosineSimilarity, cosineSimilarity(params.query_vector, 'reference_embeddings'));
                        return maxCosineSimilarity + 1.0;
                    """,
                    "params": {
                        "query_vector": query_vector
                    }
                }
            }
        }
    }
    pie = ProcessIntoES()
    response = pie.es.search(index=pie._index, body=query)
    hits = response["hits"]["hits"]
    return [hit["_source"] for hit in hits]

def cosine_similarity(x,y):
    x = np.array(x)
    y = np.array(y)
    num = x.dot(y.T)
    denom = np.linalg.norm(x) * np.linalg.norm(y)
    return num / denom

def print_sim_search_test(question, oldans, LLMans):
    docs = search_similar_documents(question, top_k=5)[0]
    question = encode_texts(question)[0]
    oldans = encode_texts(oldans)[0]
    answer = encode_texts(docs['answer'])[0]
    context = encode_texts(docs['question'])[0]
    LLMans = encode_texts(LLMans)[0]

    return {
        'Old Similarity': cosine_similarity(oldans, answer),
        'Our Similarity': cosine_similarity(LLMans, answer),
        'Context Relevance': cosine_similarity(question, answer),
        'Groundedness': cosine_similarity(question, context),
        'Answer Relevance': cosine_similarity(question, LLMans)
    }

# 函数：将字典列表转换为字符串
def convert_documents_to_string(docs):
    content = ""
    for doc in docs:
        content += "related question:"+doc['question']+"\n"
        content += "reference:"
        for ref in doc['reference']:
            content += ref+"\n"
        content += "answer:"+doc['answer']+"\n"
        content += "\n"

    return content

def qa_interface(question, docs):
    context = convert_documents_to_string(docs)
    role_msg = {"role": "user", "content": question}
    prompt_msg = {"role": "system", "content": f"通过检索可以得到以下相关内容：\n{context}"}

    messages = [
        {"role": "system", "content": "You are a helpful Chinese law assistant."},
    ]
    messages.append(role_msg)
    messages.append(prompt_msg)


    stream = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True,
        temperature=0.7,
    )
    assistant_message = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunk_message = chunk.choices[0].delta.content
            assistant_message += chunk_message
            print(chunk_message, end="", flush=True)

    messages.append({"role": "assistant", "content": assistant_message})
    print()  # 换行
    # print('ref:\n'+context)

if __name__ == "__main__":
    # 第一次运行时将数据库插入到elasticsearch当中
    # init_ES()

    while True:
        print('-'*20)
        print('-> 请输入问题：', end="")
        question = input()
        print('-'*20)
        print('◇ 检索相关内容并生成回答....\n')
        docs = search_similar_documents(question, top_k=3)
        qa_interface(question, docs)


