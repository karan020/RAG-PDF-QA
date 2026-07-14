class PromptBuilder:
    #Builds prompts for the LLM

    @staticmethod
    def build_prompt(question:str,context:str)->str:
        """ Build a RAG prompt for the LLM. 
        Parameters 
        ---------- 
        question : str 
        User question context : str 
        Retrieved document context 
        Returns 
        ------- 
        str """

        if not context.strip():
            return f""" 
            You are an intelligent document question-answering assistant. 
            The uploaded documents do not contain enough information to answer the user's question. 
            Politely respond with: 
            "I could not find this information in the uploaded documents."
             User Question: 
             {question} 
            """
        prompt=f""" 
        You are an intelligent Retrieval-Augmented Generation (RAG) assistant. 
        You MUST answer ONLY using the information provided in the CONTEXT. 
        Rules: 1. Do NOT use outside knowledge. 
        2. Do NOT make up facts. 
        3. If the answer is missing from the context, 
        say: "I could not find this information in the uploaded documents." 
        4. Keep the answer clear and concise. 
        5. Use markdown formatting. 
        6. Divide the answer into sections. 
        CONTEXT == {context} 
        USER QUESTION =={question}  
        RESPONSE FORMAT  
         # Overview Provide a short overview. --- 
         # Key Points Use bullet points. --- 
         # Detailed Explanation Explain the answer in detail using ONLY the provided context. --- 
         # Conclusion Provide a brief concluding summary. 
         Remember: 
         - Never invent information. 
         - Never answer beyond the supplied context. 
         - If information is unavailable, clearly say so. 
         """ 
        return prompt
    