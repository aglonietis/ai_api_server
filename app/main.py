# app/main.py
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from transformers import pipeline
import pyodbc
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Set up CORS middleware to allow OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# Database connection string (update with your actual values)
db_host = os.getenv("DB_HOST", "10.93.0.60")
db_port = os.getenv("DB_PORT", "1455")
db_database = os.getenv("DB_DATABASE", "Ideas")
db_user = os.getenv("DB_USER", "sa")
db_password = os.getenv("DB_PASSWORD", "Admin@123")
db_driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={db_host},{db_port};"
    f"DATABASE={db_database};"
    f"UID={db_user};"
    f"PWD={db_password};"
    f"TrustServerCertificate=yes"
)

# In-memory storage for idea embeddings
idea_data = {
    "rows": [],
}

objectives = {
    "questions": [],
    "embeddings": [],
}
sentence_similarity_model = None

# Function to load ideas from the database and store embeddings in memory

def load_idea_similarity_comparison_model():
    global sentence_similarity_model
    sentence_similarity_model = SentenceTransformer('models/all-MiniLM-L6-v2')

def load_ideas():
    logger.info("Ideas: loading")

    global idea_data
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT \
            id, \
            description, \
            status, \
            subject, \
            CreatedOn as created_at \
            FROM Ideas \
        ")

        # Fetch all ideas and compute embeddings once
        idea_data["rows"] = [{
            "id": row[0],
            "description": row[1],
            "status": row[2],
            "subject": row[3],
            "created_at": row[4],
        } for row in cursor.fetchall()]
        idea_data["descriptions"] = [row["description"] for row in idea_data["rows"]]
        idea_data["unnormalized_embeddings"] = sentence_similarity_model.encode(idea_data["descriptions"], convert_to_tensor=True)
        # Normalize embeddings to unit vectors for cosine similarity
        idea_data["embeddings"] = torch.nn.functional.normalize(idea_data["unnormalized_embeddings"], p=2, dim=1)
    logger.info("Ideas: loaded")

def load_objectives():
    logger.info("Objectives: loading")

    global objectives

    objectives["objectives"] = [
        "Specific issue or improvement that aims to address operations and contributes to overall goals",
        "Findgrid operations, processes, grid reliability or energy market would be impacted. Influence area or broadness",
        "Resources are necessary for implementation, including manpower, technology and equipment. Specific tools and skills.",
    ]
    objectives["questions"] = [
        "Can you clarify the main objective and the specific problem it is trying to solve?",
        "Can you provide more details on areas or processes it will affect?",
        "What resources (personel, technology or equipment) are required to implement this idea?"
    ]

    objectives["unnormalized_embeddings"] = sentence_similarity_model.encode(objectives["objectives"], convert_to_tensor=True)
    # Normalize embeddings to unit vectors for cosine similarity
    objectives["embeddings"] = torch.nn.functional.normalize(objectives["unnormalized_embeddings"], p=2, dim=1)

@app.on_event("startup")
def startup_event():
    load_idea_similarity_comparison_model()
    load_ideas()
    load_objectives()

# Data model for incoming similarity request
class IdeaRequest(BaseModel):
    description: str

# Similarity endpoint to find the most similar idea
@app.post("/ideas/similarity")
async def get_ideas_similarity(request: IdeaRequest):
    # Embed the input text
    unnormalized_input_embedding = sentence_similarity_model.encode(request.description, convert_to_tensor=True)
    input_embedding = torch.nn.functional.normalize(unnormalized_input_embedding, p=2, dim=0)

    similarities = util.cos_sim(input_embedding, idea_data["embeddings"]).squeeze()
    sorted_indices = torch.argsort(similarities, descending=True).tolist()

    top_3_suggestions = [
        {
            "id": idea_data["rows"][idx]["id"],
            "status": idea_data["rows"][idx]["status"],
            "subject": idea_data["rows"][idx]["subject"],
            "description": idea_data["rows"][idx]["description"],
            "created_at": idea_data["rows"][idx]["created_at"],
            "similarity_score": int(similarities[idx].item() * 100)
        } for idx in sorted_indices[:3]
    ]

    objective_similarities = util.cos_sim(input_embedding, objectives["embeddings"]).squeeze()
    filtered_indices = torch.where(objective_similarities <= 0.25)[0]

    questions_to_ask = [
        objectives["questions"][idx] for idx in filtered_indices
    ]

    return {
        "data": top_3_suggestions,
        "questions_to_ask": questions_to_ask,
    }