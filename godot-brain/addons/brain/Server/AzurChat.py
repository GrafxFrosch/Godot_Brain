
from langchain_openai import AzureChatOpenAI

def getAzure():
    return AzureChatOpenAI(
        model="gpt-4o-mini"
    )
