from openai import OpenAI

client = OpenAI(
    base_url = 'https://generativelanguage.googleapis.com/v1beta',
    api_key='AIzaSyCkmT3FR5MIxMqGLZnL8u2Nt_Hv7YYzQTo', # required, but unused
)

response = client.chat.completions.create(
  model="gemini-1.5-flash",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "assistant", "content": "The LA Dodgers won in 2020."},
    {"role": "user", "content": "tell more about Elon Musk"}
  ]
)

print(response.choices[0].message.content)