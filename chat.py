# This is the full content of chat.py
# This script is designed to work with YOUR bedrock_utils.py file.

# We import all the functions you provided
from bedrock_utils import (
    valid_prompt, 
    query_knowledge_base, 
    generate_response
)

def build_rag_prompt(user_prompt, context_chunks):
    """
    This is the missing RAG logic.
    It manually builds a prompt that includes the retrieved context.
    """
    
    # 1. Start with the system instruction
    prompt_template = """Human: You are an expert assistant on heavy machinery.
    Use the following pieces of context to answer the user's question.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    <context>
    {context}
    </context>
    
    <question>
    {question}
    </question>
    
    Assistant:
    """
    
    # 2. Add the retrieved document chunks to the context
    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"Chunk {i+1}:\n{chunk['content']['text']}\n\n"
        
    # 3. Inject the context and question into the template
    final_prompt = prompt_template.format(
        context=context_text,
        question=user_prompt
    )
    
    return final_prompt, context_chunks

def get_rag_response(user_prompt):
    """
    This is the main function that orchestrates the RAG flow.
    It completes the "generate_response" wrapper requirement.
    """
    
    # 1. Validate the prompt (using your function)
    print("Bot: Validating prompt...")
    if not valid_prompt(user_prompt):
        return "I'm sorry, I can only answer questions related to heavy machinery. Please try another question."

    # 2. Retrieve documents from the Knowledge Base (using your function)
    print("Bot: Retrieving information...")
    context_chunks = query_knowledge_base(user_prompt)
    
    if not context_chunks:
        return "I'm sorry, I couldn't find any relevant information in the knowledge base for your question."
        
    # 3. Build the final prompt with the retrieved context
    final_prompt, sources = build_rag_prompt(user_prompt, context_chunks)
    
    # 4. Generate the final answer (using your function)
    print("Bot: Generating answer...")
    answer = generate_response(final_prompt)
    
    # 5. Format the response with source citations
    response_text = f"{answer}\n\nSources:\n"
    source_files = set() # Use a set to avoid duplicate file names
    
    for chunk in sources:
        try:
            s3_uri = chunk['location']['s3Location']['uri']
            file_name = s3_uri.split('/')[-1]
            source_files.add(file_name)
        except (KeyError, IndexError, TypeError):
            continue
            
    for i, file_name in enumerate(source_files, 1):
        response_text += f"[{i}] {file_name}\n"

    return response_text


def main_chat_loop():
    print("==================================================")
    print("  Welcome to the Knowledge Base Chat Application! ")
    print("==================================================")
    print("(Using your custom bedrock_utils.py file)")
    print("Type 'quit' or 'exit' to end the chat.")
    print("\n")
    
    while True:
        try:
            # 1. Get input from the user
            user_prompt = input("You: ")
            
            # 2. Check for exit command
            if user_prompt.lower() in ['quit', 'exit']:
                print("Chat ended. Goodbye!")
                break
                
            # 3. Get the RAG response
            bot_response = get_rag_response(user_prompt)
            
            # 4. Print the response
            print(f"\nBot: {bot_response}\n")
            print("--------------------------------------------------")

        except EOFError:
            print("\nChat ended. Goodbye!")
            break
        except KeyboardInterrupt:
            print("\nChat interrupted. Goodbye!")
            break

# This makes the script runnable
if __name__ == "__main__":
    main_chat_loop()
