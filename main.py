import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse,StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional,List,Dict
import shutil
import uvicorn
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

#Load environment variables
load_dotenv()

# Import modules
from modules.pdf_loader import PDFLoader
from modules.cleaner import TextCleaner
from modules.chunker import TextChunker
from modules.embeddings import EmbeddingModel
from modules.vector_db import VectorDatabase
from modules.retriever import Retriever
from modules.prompt import PromptBuilder
from modules.llm import GroqLLM
from modules.utils import Utils
from modules.mongodb import get_db

#Import models
from modules.models import(
    UserCreatedRequest,
    ChatCreateRequest,
    ChatRenameRequest,
    ConversationRequest,
    ChatResponse,
    ConversationResponse,
    User,
    Chat,
    Conversation
)
#Legacy/Simple Models(for backward compatibility)
class QuestionRequest(BaseModel):
    #Simple question request for non-chat endpoints.
    question: str
    top_k: Optional[int] = 5

class ProcessResponse(BaseModel):
    #Response for PDF processing.
    message: str
    chunks_created: int
    vectors_stored: int
    pages_processed:Optional[int]=None
    filename:Optional[str]=None

class SimpleChatRequest(BaseModel):
    #Simple chat request without user management.
    question:str
    top_k:Optional[int]=5

class SimpleChatResponse(BaseModel):
    #Simple chat response
    answer:str
    sources:List[Dict]
    chunks_used:int

app = FastAPI(title="PDF RAG QA API", version="2.0", description="API for PDF Questions Answering with chat history and streaming")

#Add CORS middleware - Fixed :using CORSMiddleware (not CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components

pdf_loader = PDFLoader()
text_cleaner = TextCleaner()
text_chunker = TextChunker()
embedding_model = EmbeddingModel()
vector_db = VectorDatabase()

# Load vector database if it exists
try:
    vector_db.load()
    print("✅ Vector database loaded successfully")
except FileNotFoundError:
    print("ℹ️ No existing vector database found. Upload a PDF to create one.")

retriever = Retriever(embedding_model, vector_db)
prompt_builder = PromptBuilder()

#Initialized MongoDB Singleton
db=get_db()#Singleton instance  
print("✅ MongoDB Singleton initialized")

# Initialize LLM (will fail if GROQ_API_KEY is not set)
try:
    llm = GroqLLM()
    print("✅ LLM initialized successfully")
except Exception as e:
    print(f"⚠️ LLM initialization failed: {e}")
    llm = None

#Streaming Helpers
async def stream_generator(chat_id:str,question:str,prompt:str,retrieval_result:dict):
    #Generator for streaming response with SSE format.
    full_answer=" "

    try:
        #Send sources first
        yield f"data:{json.dumps({'type':'sources','data':retrieval_result['sources']})}\n\n"

        #Stream the answer word by word
        if llm:
            for chunk in llm.stream_answer(prompt):
                full_answer+=chunk
                yield f"data:{json.dumps({'type':'chunk','data':chunk})}\n\n"
                await asyncio.sleep(0.01)


        #Save conversation to database
        conversation=db.add_conversation(
            chat_id=chat_id,
            question=question,
            answer=full_answer,
            sources=retrieval_result["sources"]
        )

        #Send completion with conversation ID
        yield f"data:{json.dumps({'type':'done','data':'Stream complete','conversation_id':conversation.get('_id') if conversation else None})}\n\n"

    except Exception as e:
        error_msg=f"Error during streaming :{str(e)}"
        print(f"❌ {error_msg}")
        yield f"data: {json.dumps({'type':'error','data':error_msg})}\n\n"


#Simple/Legacy Endpoint(No User Management)
@app.post("/ask",response_model=SimpleChatResponse)
async def simple_ask(request: QuestionRequest):
    #Simple ask endpoints without user/chat mangement.
    #useful for quick testing.

    try:
        question=request.question.strip()
        print(f"❓ Simple Question:{question}")

        if not question:
            raise HTTPException(status_code=400,detail="Question cannot empty")
        
        if vector_db.total_vectors()==0:
            raise HTTPException(status_code=400,detail="No document uploaded. Please upload a PDF first.")
        
        if llm is None:
            raise HTTPException(status_code=500,detail="LLM not initialized.")
        

        #Retrieve context with top_k=5 (fixed)
        retrieval_result=retriever.retrieve_context(question,top_k=5)
        print(f"📚 Retrieved {len(retrieval_result['chunks'])}chunks")

        #Build prompt and generate answer
        prompt=prompt_builder.build_prompt(question,retrieval_result["context"])
        answer=llm.generate_answer(prompt)
        print(f"✅ Generated answer({len(answer)}characters)")

        return SimpleChatResponse(
            answer=answer,
            sources=retrieval_result["sources"],
            chunks_used=len(retrieval_result["chunks"])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error :{str(e)}")
        raise HTTPException(status_code=500,detail=str(e))

@app.post("/ask/stream")
async def simple_ask_stream(request: QuestionRequest):
    #Simple streaming ask endpoint without user/chat management.
    try:
        question=request.question.strip()
        print(f"❓ Stream simple Question:{question}")

        if not question:
            raise HTTPException(status_code=400,detail="Question cannot be empty")

        if vector_db.total_vectors()==0:
            raise HTTPException(status_code=400,detail="No document uploaded. Please uploaded PDF first.")

        if llm is None:
            raise HTTPException(status_code=500,detail="LLM not initialized")
        
        #Retrieve context with top_k=5
        retrieval_result=retriever.retrieve_context(question,top_k=5)
        print(f"📚 Retrieved {len(retrieval_result['chunks'])} chunks")

        #Build Prompt
        prompt=prompt_builder.build_prompt(question,retrieval_result["context"])

        async def simple_stream_generator():
            full_answer=" "

            #Send sources first
            yield f"data :{json.dumps({'type':'sources','data':retrieval_result['sources']})}\n\n"

            #Stream sources first
            for chunk in llm.stream_answer(prompt):
                full_answer+=chunk
                yield f"data:{json.dumps({'type':'chunk','data':chunk})}\n\n"
                await asyncio.sleep(0.01)

            yield f"data: {json.dumps({'type':'done','data':'Stream complete'})}\n\n"

        return StreamingResponse(
            simple_stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control":"no-cache",
                "Connection":"keep-alive",
                "X-Accel-Buffering":"no",
                "Content-Type":"text/event-stream"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error :{str(e)}")
        raise HTTPException(status_code=500,detail=str(e))
    




#User Endpoint
@app.post("/user/create")
async def create_user(request:UserCreatedRequest):
    #Create a new User.

    try:
        #Check if user exists
        existing=db.get_user_by_username(request.username)
        if existing:
            return JSONResponse(
                status_code=400,
                content={"error ":"Username already exists"}
            )
        
        #Create user
        user_data=db.create_user(request.username,request.email)


        #Convert to User Model
        user=User(
            id=user_data["_id"],
            username=user_data["username"],
            email=user_data.get("email"),
            chat_ids=user_data.get("chats",[]),
            created_at=user_data["created_at"]
        )

        return {
            "message":"User created successfully",
            "user":user.dict(),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":str(e)})
    
@app.get("/user/{user_id}")
async def get_user(user_id:str):
    #Get user details by ID.
    try:
        user_data=db.get_user(user_id)
        if not user_data:
            return JSONResponse(status_code=404,content={"error":"User not found"})
        
        user=User(
            id=user_data["_id"],
            username=user_data["username"],
            email=user_data.get("email"),
            chat_ids=user_data.get("chats",[]),
            created_at=user_data["created_at"]
        )

        return {"user":user.dict()}
    
    except Exception as e:
        return JSONResponse(status_code=500,content={"error":str(e)})

@app.get("/user/by-username/{username}")
async def get_user_by_username(username:str):
    #Get user details by username (for login).
    try:
        user_data=db.get_user_by_username(username)
        if not user_data:
            return JSONResponse(status_code=404,content={"error":"User not found"})
        
        user=User(
            id=user_data["_id"],
            username=user_data["username"],
            email=user_data.get("email"),
            chat_ids=user_data.get("chats",[]),
            created_at=user_data["created_at"]
        )

        return {"user":user.dict()}
    
    except Exception as e:
        return JSONResponse(status_code=500,content={"error":str(e)})
    
@app.get("/user/{user_id}/chats")
async def get_user_chats(user_id:str):
    #Get all chats for a user.
    try:
        chats_data=db.get_user_chats_summary(user_id)

        #Convert to Chatresponse Models
        chats=[]
        for chat in chats_data:
            chats.append(ChatResponse(
                id=chat["id"],
                name=chat["name"],
                pdf_filename=chat["pdf_filename"],
                conversation_count=chat["conversation_count"],
                created_at=chat["created_at"],
                updated_at=chat["updated_at"]
            ))

        return{"chats":[chat.dict() for chat in chats]}
    
    except Exception as e:
        return JSONResponse(status_code=500,content={"error":str(e)})





#PDF Endpoints

@app.post("/upload",response_model=ProcessResponse)
async  def upload_pdf(file:UploadFile=File(...)):
    #Upload and process a PDF File.

    try:
        print(f"📄 Received file:{file.filename}")

        #Validation file Type
        if not Utils.allowed_file(file.filename):
            return JSONResponse(status_code=400, content="Only PDF files are supported.")
        

        #Save File - read async file content
        content = await file.read()
        file_path = pdf_loader.save_uploaded_bytes(file.filename, content)
        print(f"💾 Saved to:{file_path}")

        #Extract text
        pages=pdf_loader.extract_text(file_path)
        print(f"📝 Extracted {len(pages)}pages")
        if not pages:
            return JSONResponse(
                status_code=400,
                content={"error":"No text could be extracted from the PDF"}
            )
        
        #Clean Text
        cleaned_pages=text_cleaner.clean_pages(pages)
        print(f"🧹 Cleaned:{len(cleaned_pages)}pages")

        #Chunk Text
        chunks=text_chunker.chunk_pages(cleaned_pages)
        print(f"🧩 Created {len(chunks)}chunks")

        if not  chunks:
            return JSONResponse(
                status_code=400,
                content={"error":"No chunks could be created"}
            )
        
        #Generate Embeddings
        embeddings=embedding_model.embed_documents(chunks)
        print(f"🔢 Generated {embeddings.shape[0]}embedddings")

        #Store in vector daatabase
        vector_db.add_documents(embeddings,chunks)
        vector_db.save()
        print(f"💾 Saved to vector database")

        return ProcessResponse(
            message=f"Successfully processed {file.filename}",
            chunks_created=len(chunks),
            vectors_stored=vector_db.total_vectors(),
            pages_processed=len(pages),
            filename=file.filename
        )
    
    except Exception as e:
        print(f"❌ Error :{str(e)}")

        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500,
                            content={"error":str(e)})
    


#Chat Endpoint

@app.post("/chat/create")
async def create_chat(request: ChatCreateRequest):
    #Create a new chat for a user
    try:
        #Check if user exists
        user_data=db.get_user(request.user_id)
        if not user_data:
            return JSONResponse(
                status_code=404,
                content={"error":"User Not Found"}
            )
        
        #Check if PDF exists
        pdf_path=os.path.join("uploads",request.pdf_filename)
        if not os.path.exists(pdf_path):
            return JSONResponse(
                status_code=400,
                content={"error": "PDF file not found. Please upload the PDF first."}
            )
        
        #Create chat
        chat_data=db.create_chat(
            user_id=request.user_id,
            name=request.name,
            pdf_filename=request.pdf_filename,
            pdf_path=pdf_path
        )

        #Convert to chat model
        chat=Chat(
            id=chat_data["_id"],
            user_id=chat_data["user_id"],
            name=chat_data["name"],
            pdf_filename=chat_data["pdf_filename"],
            pdf_path=chat_data["pdf_path"],
            conversation_ids=chat_data.get("Conversation",[]),
            created_at=chat_data["created_at"],
            updated_at=chat_data["updated_at"],
            is_active=chat_data.get("is_active",True)
        )

        return{
            "message":"Chat created sucessfully",
            "chat":chat.dict()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error":str(e)}
        )
    
@app.get("/chat/{chat_id}")
async def get_chat(chat_id:str):
    #Get chat details with all conversation.
    try:
        chat_data=db.get_chat(chat_id)
        if not chat_data:
            return JSONResponse(status_code=404,content={"error":"Chat not found"})
        

        # Convert Conversations
        conversations = []
        for conv_data in chat_data.get("conversations", []):
            conv = Conversation(
                id=conv_data.get("_id"),
                chat_id=conv_data.get("chat_id"),
                question=conv_data.get("question"),
                answer=conv_data.get("answer"),
                sources=conv_data.get("sources", []),
                created_at=conv_data.get("created_at")
            )
            conversations.append(conv.dict())

        
        #Create chat with conversation
        chat=Chat(
            id=chat_data["_id"],
            user_id=chat_data["user_id"],
            name=chat_data["name"],
            pdf_filename=chat_data["pdf_filename"],
            conversation_ids=[c["id"] for c in conversations if c.get("id")],
            created_at=chat_data["created_at"],
            updated_at=chat_data["updated_at"],
            is_active=chat_data.get("is_active",True)          
        )

        return {
            "chat":chat.dict(),
            "conversations":conversations
        }
    except Exception as e:
        return JSONResponse(status_code=500,content={"error":str(e)})
    
@app.put("/chat/rename")
async def rename_chat(request: ChatRenameRequest):
    #Rename A Chat
    try:
        result=db.rename_chat(request.chat_id,request.new_name)
        if result:
            return {"message":"Chat rename successfully"}
        return JSONResponse(status_code=404,content={"error":"Chat not found"})
    except Exception as e:
        return JSONResponse(status_code=500,content={"error":str(e)})
    
@app.delete("/chat/{chat_id}")
async def delete_chat(chat_id:str):
    #Delete a chat
    try:
        result=db.delete_chat(chat_id)
        if result:
            return {"message":"Chat deleted successfully"}
        return JSONResponse(status_code=404,content={"error":"Chat not found"})
    
    except Exception as e:
        return JSONResponse(status_code=500,content={"error":str(e)})
    


#Conversation Endpoint
@app.post("/conversation/ask")
async def ask_question(request:ConversationRequest):
    #Ask a question and get response (non-streaming)
    try:
        question=request.question.strip()
        print(f"❓ Question: {question}")

        if not question:
            return JSONResponse(
                status_code=400,
                content={"error":"Question cannot be empty"}
            )   
        
        #Get Chat
        chat_data=db.get_chat(request.chat_id)
        if not chat_data:
            return JSONResponse(status_code=400,content={"error":"Chat not found"})
        
        #Check if LLM is available
        if llm is None:
            return JSONResponse(status_code=500,content={"error":"LLM not initialized"})
        
        #Get conversation history
        conversation_history = chat_data.get("conversations", [])
        
        #Retrieve context(top_k=5)
        retrieval_result=retriever.retrieve_context(question,top_k=5)
        print(f"📚 Retrieved {len(retrieval_result['chunks'])}chunks")

        #Build prompt with conversation history and generate answer
        prompt=prompt_builder.build_prompt(question,retrieval_result["context"],conversation_history)
        answer=llm.generate_answer(prompt)
        print(f"✅ Generated answer ({len(answer)}characters)")

        #Save conversation
        conv_data=db.add_conversation(
            chat_id=request.chat_id,
            question=question,
            answer=answer,
            sources=retrieval_result["sources"]
        )

        #convert to Conversation model
        conversation=Conversation(
            id=conv_data["_id"],
            chat_id=conv_data["chat_id"],
            question=conv_data["question"],
            answer=conv_data["answer"],
            sources=conv_data.get("sources",[]),
            created_at=conv_data["created_at"]
        )

        return{
            "conversation":conversation.dict(),
            "sources":retrieval_result["sources"],
            "chunks_used":len(retrieval_result["chunks"])
        }
    except Exception as e:
        print(f"❌ Error :{str(e)}")
        return JSONResponse(status_code=500,content={"error":str(e)})

@app.post("/conversation/ask/stream")
async def ask_question_stream(request:ConversationRequest):
    #Ask a question and get streaming response
    try:
        question=request.question.strip()
        print(f"❓ Stream Question: {question}")

        if not question:
            return JSONResponse(
                status_code=400,
                content={"error":"Question cannot be empty"}
            )
        
        #Get Chat
        chat_data=db.get_chat(request.chat_id)
        if not chat_data:
            return JSONResponse(status_code=400,content={"error":"Chat not found"})
        
        #Check if LLM is available
        if llm is None:
            return JSONResponse(status_code=500,content={"error":"LLM not initialized"})
        
        #Get conversation history
        conversation_history = chat_data.get("conversations", [])
        
        #Retrieve context(top_k=5)
        retrieval_result=retriever.retrieve_context(question,top_k=5)
        print(f"📚 Retrieved {len(retrieval_result['chunks'])} chunks")

        #Build Prompt with conversation history
        prompt=prompt_builder.build_prompt(question,retrieval_result["context"],conversation_history)

        async def conversation_stream_generator():
            full_answer=" "

            #Send sources first
            yield f"data:{json.dumps({'type':'sources','data':retrieval_result['sources']})}\n\n"

            #Stream the answer word by word
            for chunk in llm.stream_answer(prompt):
                full_answer+=chunk
                yield f"data:{json.dumps({'type':'chunk','data':chunk})}\n\n"
                await asyncio.sleep(0.01)

            #Save conversation to database
            conversation=db.add_conversation(
                chat_id=request.chat_id,
                question=question,
                answer=full_answer,
                sources=retrieval_result["sources"]
            )

            #Send completion with conversation ID
            yield f"data:{json.dumps({'type':'done','data':'Stream complete','conversation_id':conversation.get('_id') if conversation else None})}\n\n"

        return StreamingResponse(
            conversation_stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control":"no-cache",
                "Connection":"keep-alive",
                "X-Accel-Buffering":"no",
                "Content-Type":"text/event-stream"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error :{str(e)}")
        raise HTTPException(status_code=500,detail=str(e))


# Main Execution

if __name__=="__main__":
    port=int(os.getenv("PORT",8000))
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        reload=False
    )