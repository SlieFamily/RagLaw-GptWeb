import os
from elasticsearch import Elasticsearch
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

def encode_texts(texts):
    inputs = tokenizer(" ".join(texts), padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)
    return embeddings.numpy().tolist()

class ProcessIntoES:
    def __init__(self):
        self._index = "crime_data"
        self.es = Elasticsearch([{"host": "127.0.0.1", "port": 9200, 'scheme': 'http'}]) # 需要指定协议
        self.doc_type = "crime"
        cur = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.music_file = os.path.join(cur, 'data/qa_with_ref_92k.json') # 'data/qa_corpus.json'


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

    # messages.append({"role": "assistant", "content": assistant_message})

    return assistant_message #+'\n---\n相关引用:\n'+context