import os 
from dotenv import load_dotenv
from groq import Groq

#Load Environment Variable
load_dotenv()

class GroqLLM:
    #Handels Communication with the Groq LLM.

    def __init__(self):
        self.api_key=os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Please check your .env file"
            )
        
        self.model=os.getenv(
            "LLM_MODEL",
            "llama-3.3-70b-versatile"
        )
        self.client=Groq(api_key=self.api_key)

    #Generate Answer

    def generate_answer(self,prompt:str,temperature:float=0.2,max_token:int=1024)->str:
        #Send prompt to Groq and return the generate answer.

        try:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role":"system",
                        "content":(
                            "You are an expert Retrieval-Augmented " 
                            "Generation (RAG) assistant. " 
                            "Answer ONLY from the provided context."
                        ),
                    },
                    {
                        "role":"user",
                        "content":prompt,
                    },
                ],
                temperature=temperature,
                max_tokens=max_token,
            )

            return response.choices[0].message.content
        
        except Exception as e:
            raise RuntimeError(
                f"Groq API Error:{str(e)}"
            )

    #Streaming Answer
    def stream_answer(self,propmt:str,temperature:float=0.2,max_token:int=1024):

        #Stream the response token by token
        #Useful for Streamlit
        try:
            stream=self.client.chat.completions.create(
              model=self.model,
            
              messages=[
                {
                    "role":"system",
                    "content":(
                        "You are an expert Retrival-Argyument"
                        "Generation (RAG)assistant"
                    ),
                },
                {
                    "role":"user",
                    "content":prompt,
                },
                 ],
               temperature=temperature,
               max_token=max_token,
               stream=True,
            )

            for chunk in stream:
              if(
                chunk.choices
                and chunk.choices[0].delta.content
                ):
                  yield chunk.choices[0].delta.content

    
        except Exception as e:
            raise RuntimeError(
            f"Groq Streaming Error: {str(e)}"
            )
        
    #Check Connection
    def test_connection(self):
        #Verify that the Groq API is working .
        try:

            response=self.client.chat.completions.create(
                model=self.model,

                messages=[
                    {
                        "role":"user",
                        "content":"Reply with only the word:Connected",
                    }
                ],
                max_token=5
            )

            return response.choices[0].message.content
        
        except Exception as e:
            return f"Connection Failed:{e}"
    