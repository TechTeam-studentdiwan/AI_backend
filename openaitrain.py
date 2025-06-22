from openai import OpenAI
client = OpenAI(
    api_key="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"
)


res = client.files.create(
  file=open("data.txt", "rb"),
  purpose="user_data"
)

print(res)


vector_store = client.vector_stores.create(
  name="test store"
)
print(vector_store)

vector_store_file = client.vector_stores.files.create(
  vector_store_id='vs_6856828126908191b6d5441d82849847',
  file_id='file-7MHwAfoXmrZob4YK1jdBEU'
)

response = client.responses.create(
    model="gpt-4.1-mini",
    tools=[{
      "type": "file_search",
      "vector_store_ids": ["vs_6856828126908191b6d5441d82849847"],
      "max_num_results": 20
    }],
    input="Where is hospital located?",
)