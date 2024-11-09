# app/main.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
import pyodbc
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import os


app = FastAPI()

# Set up CORS middleware to allow OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS
    allow_headers=["*"],  # Allows all headers
)

# Load the model for embedding
# model = SentenceTransformer('all-MiniLM-L6-v2')
model = SentenceTransformer('models/all-MiniLM-L6-v2')

# Database connection string (update with your actual values)
db_host = os.getenv("DB_HOST", "10.87.3.162")
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

# Function to load ideas from the database and store embeddings in memory
def load_ideas():
    print("Loading Ideas")

    global idea_data
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT \
            id, \
            description, \
            (SELECT IdeaStatuses.Name FROM IdeaStatuses WHERE IdeaStatuses.Id = Ideas.IdeaStatusId) AS status, \
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
        idea_data["unnormalized_embeddings"] = model.encode(idea_data["descriptions"], convert_to_tensor=True)
        # Normalize embeddings to unit vectors for cosine similarity
        idea_data["embeddings"] = torch.nn.functional.normalize(idea_data["unnormalized_embeddings"], p=2, dim=1)
    print("Finished loading ideas")

load_ideas()

# Data model for incoming similarity request
class IdeaRequest(BaseModel):
    description: str

# Similarity endpoint to find the most similar idea
@app.post("/ideas/similarity")
async def get_ideas_similarity(request: IdeaRequest):
    # Embed the input text
    unnormalized_input_embedding = model.encode(request.description, convert_to_tensor=True)
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

    return {
        "data": top_3_suggestions,
    }