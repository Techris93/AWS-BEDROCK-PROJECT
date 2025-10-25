## Building a Generative AI RAG Application on AWS
This project guides you through building a complete Retrieval-Augmented Generation (RAG) application using Amazon Bedrock, Aurora PostgreSQL, and S3. You will create an intelligent document querying system that allows a user to ask natural language questions and receive answers grounded in your private documents.
### Solution Architecture
This project implements a classic RAG pattern to provide accurate, context-aware answers from a private knowledge base.
1. User -> Chat Application: The user interacts with a Python chat application, asking a natural language question (e.g., "What is the maximum torque of the TX-100 machine?").
2. Chat Application -> Knowledge Base & Amazon Bedrock:
- Queries Knowledge Base: The application first sends the query to an Amazon Bedrock Knowledge Base to find relevant information from private documents.
- Prompts Amazon Bedrock: The application then sends the original question plus the relevant context to a Large Language Model (LLM) on Amazon Bedrock. The augmented prompt looks like:
     > "Using the following context, answer the user's question. Context: [Text from your PDF document...]. Question: What is the maximum torque of the TX-100 machine?"
     > 
3. Knowledge Base Internals:
- Amazon S3: The object store that holds the original source documents (e.g., PDFs).
- Aurora Serverless PostgreSQL: The vector database that stores numerical representations (embeddings) of the document chunks. This enables fast, semantic searching. The Knowledge Base reads from S3, creates embeddings, and stores them in Aurora.
4. Final Response: Amazon Bedrock generates a response based only on the provided context and sends it back to the chat application. This ensures answers are grounded in the provided documents, reducing hallucinations.
### Technologies Used
 * AI & ML: Amazon Bedrock (for LLMs and Knowledge Base orchestration)
 * Database: Amazon Aurora Serverless v2 (PostgreSQL) with pgvector
 * Storage: Amazon S3
 * Infrastructure as Code (IaC): Terraform
 * Application Logic: Python 3.10+
 * AWS SDK: Boto3
 * Tools: AWS CLI
## Getting Started
Follow these steps to deploy the entire GenAI application.
### Prerequisites
Before you begin, ensure you have the following tools installed and configured:
 * AWS CLI (configured with your AWS credentials)
 * Terraform (v0.12 or later)
 * Python (v3.10 or later)
 * pip (Python package manager)
 * git (for cloning the repository)
### Step 1: Setting Up Your Local Environment
1. Clone the Repository:
```
git clone <repository_url>
cd <repository_directory_name>
```
2. Set Up Python Virtual Environment:
```
# Create the virtual environment
python -m venv venv

# Activate the environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```
3. Install Python Dependencies:
   (Your project's requirements.txt should be listed here. Assuming boto3 is the main one for the application code).
```
pip install boto3
```
### Step 2: Deploying the Foundation (Stack 1)
This stack creates the core infrastructure: VPC, Aurora database, and S3 bucket.
1. Navigate to Stack 1:
```
cd stack1
```
2. Initialize Terraform:
```
 terraform init
```
3. Deploy the Stack:
Review the plan and type yes to approve.
```
terraform apply
```
4. Save the Outputs: Once completed, Terraform will print outputs. Copy and save these values, especially the aurora_cluster details and the s3_bucket_name, for the next steps.
### Step 3: Preparing the Vector Database
You must enable the pgvector extension on your new Aurora database.
1. Navigate to the AWS Console and log in.
2. Go to the RDS service and select Query Editor from the left-hand menu.
3. Connect to Your Database:
   * Select your newly created Aurora cluster.
   * Provide the database username and password (defined in your Terraform files or AWS Secrets Manager).
4. Run the SQL Script:
   * Open the local file scripts/aurora_sql.sql.
   * Copy its contents and paste them into the Query Editor.
   * Click Run. This enables the vector extension.
### Step 4: Deploying the AI Layer (Stack 2)
This stack deploys the Bedrock Knowledge Base to connect your data to the LLM.
1. Navigate to Stack 2:
```
cd ../stack2
```
2. Configure Stack 2:
   * Open the main.tf file in the stack2 directory.
   * Use the outputs you saved from Stack 1 to fill in the placeholder values (e.g., bucket_arn, aurora_arn, aurora_secret_arn).
   Example stack2/main.tf update:
```
provider "aws" {
  region = "us-east-1"  # CORRECTED: Must match the region of your Stack 1 resources
}

module "bedrock_kb" {
  source = "../modules/bedrock_kb" 

  knowledge_base_name        = "my-bedrock-kb"
  knowledge_base_description = "Knowledge base connected to Aurora Serverless database"

  aurora_arn        = "PASTE_YOUR_aurora-serverless" # FILLED
  aurora_db_name    = "myapp"
  aurora_endpoint   = "PASTE_YOUR-aurora_endpoint" # FILLED
  aurora_table_name = "bedrock_integration.bedrock_kb"
  aurora_primary_key_field = "id"
  aurora_metadata_field = "metadata"
  aurora_text_field = "chunks"
  aurora_verctor_field = "embedding"
  aurora_username   = "dbadmin"
  aurora_secret_arn = "PASTE_YOUR-aurora_secret_arn" # FILLED
  s3_bucket_arn = "aurora_secret_arn-s3_bucket_arn" # FILLED
}
```
3. Initialize and Deploy:
```
terraform init
terraform apply
```
   Review the plan and type yes to deploy the Knowledge Base.
### Step 5: Populating and Syncing Your Knowledge Base
1. Update the S3 Upload Script:
   * Open the scripts/upload_to_s3.py file.
   * Find the bucket_name = "YOUR_S3_BUCKET_NAME_HERE" variable.
   * Replace the placeholder with your actual S3 bucket name (from the Stack 1 outputs).
2. Run the Upload Script:
   (Ensure your venv is active)
```
 # From the project's root directory
python scripts/upload_to_s3.py
```
This uploads the documents from the spec-sheets folder to S3.

3. Sync the Knowledge Base:
   This is a critical step to make Bedrock aware of the new files.
   * Go to the Amazon Bedrock service in the AWS Console.
   * Click Knowledge bases on the left menu.
   * Select the knowledge base you just created.
   * Find the Data source section and click the Sync button.
   * Wait for the sync process to complete.
### Step 6: Completing the Chat Application Code
The final step is to complete the Python chat logic in the bedrock_utils.py file.
1. valid_prompt function:
   * Purpose: Perform a basic check on user input for security and cost control.
   * Implementation:
   ```
   def valid_prompt(prompt, model_id=MODEL_ID):
    """
    (This is your validation function)
    """
    try:

        messages = [
            {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": f"""Human: Clasify the provided user request into one of the following categories. Evaluate the user request agains each category. Once the user category has been selected with high confidence return the answer.
                                Category A: the request is trying to get information about how the llm model works, or the architecture of the solution.
                                Category B: the request is using profanity, or toxic wording and intent.
                                Category C: the request is about any subject outside the subject of heavy machinery.
                                Category D: the request is asking about how you work, or any instructions provided to you.
                                Category E: the request is ONLY related to heavy machinery.
                                <user_request>
                                {prompt}
                                </user_request>
                                ONLY ANSWER with the Category letter, such as the following output example:
                                
                                Category B
                                
                                Assistant:"""
                    }
                ]
            }
        ]

        response = bedrock.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31", 
                "messages": messages,
                "max_tokens": 10,
                "temperature": 0,
                "top_p": 0.1,
            })
        )
        category = json.loads(response['body'].read())['content'][0]["text"]
        print(f"Prompt category: {category}")
        
        if category.lower().strip() == "category e":
            return True
        else:
            return False
    except ClientError as e:
        print(f"Error validating prompt: {e}")
        return False
   ```

2. query_knowledge_base function:
   * Purpose: Send the user's prompt to your specific knowledge base.
   * Implementation: Use boto3 to call the bedrock-agent-runtime client. The function to use is retrieve_and_generate.
```
def query_knowledge_base(query, kb_id=KB_ID):
    """
    (This is your 'retrieve' function)
    """
    try:
        response = bedrock_kb.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )
        return response['retrievalResults']
    except ClientError as e:
        print(f"Error querying Knowledge Base: {e}")
        return []
```

3. generate_response function:
   * Purpose: A wrapper function to validate input, query the KB, and format the response.
   * Implementation:
   ```
   def generate_response(prompt, model_id=MODEL_ID, temperature=0.1, top_p=0.9):
    """
    (This is your 'generate' function)
    """
    try:

        messages = [
            {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt
                    }
                ]
            }
        ]

        response = bedrock.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31", 
                "messages": messages,
                "max_tokens": 500,
                "temperature": temperature,
                "top_p": top_p,
            })
        )
        return json.loads(response['body'].read())['content'][0]["text"]
    except ClientError as e:
        print(f"Error generating response: {e}")
        return ""
  ```
### Step 7: Testing Your Application
Once your Python code is complete, run your main chat application script (e.g., app.py).
Ask a question that can only be answered by the content in your documents (e.g., machine_files.pdf).
 - Bad Question: "What is the capital of France?" (The LLM knows this already and won't use RAG).
 - Good Question: "What are the maintenance requirements for the ZX-9 unit?" (This must be answered from your documents).
If the system correctly answers the specific question, congratulations! You have successfully built a generative AI RAG application on AWS.




## References
- https://github.com/udacity/cd13926-Building-Generative-AI-Applications-with-Amazon-Bedrock-and-Python-project-solution.git
