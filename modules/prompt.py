class PromptBuilder:
    """Builds prompts for the LLM."""

    @staticmethod
    def build_prompt(question: str, context: str, conversation_history: list = None) -> str:
        """Build a conversational RAG prompt for the LLM.

        Parameters
        ----------
        question : str
            User question.
        context : str
            Retrieved document context.
        conversation_history : list
            List of previous conversation turns.

        Returns
        -------
        str
            The complete prompt string.
        """

        # No relevant context found
        if not context.strip():
            return (
                "You are a helpful document assistant. "
                "The uploaded document does not contain information relevant to this question. "
                "Respond naturally: tell the user you couldn't find that information in the document "
                "and invite them to ask something else.\n\n"
                f"User: {question}\nAssistant:"
            )

        # Build conversation history string (last 3 turns for context)
        history_str = ""
        if conversation_history and len(conversation_history) > 0:
            history_str = "\n--- Recent conversation ---\n"
            for conv in conversation_history[-3:]:
                history_str += f"User: {conv['question']}\n"
                history_str += f"Assistant: {conv['answer'][:400]}\n\n"
            history_str += "--- End of recent conversation ---\n"

        prompt = f"""You are a helpful, friendly AI assistant that answers questions based on an uploaded PDF document.

Speak naturally and conversationally — like ChatGPT. Do NOT use rigid report sections such as "Overview", "Key Points", "Detailed Explanation", or "Conclusion" unless the user explicitly asks for a structured breakdown.

Guidelines:
- Answer directly and clearly in plain language.
- Use short paragraphs or bullet points only when it genuinely aids clarity.
- If the answer is not in the document, say so honestly and briefly.
- Never invent or assume information not present in the context.
- Reference the conversation history if it helps give a more useful answer.
- For simple or conversational questions (e.g. "hi", "thanks", "what is this about?"), reply in a short, friendly way.

{history_str}
--- Document context ---
{context}
--- End of context ---

User: {question}
Assistant:"""

        return prompt
