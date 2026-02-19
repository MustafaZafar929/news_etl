import os
import uuid
import numpy as np
import psycopg2
from dagster import asset, Output, Definitions, ScheduleDefinition, define_asset_job, DefaultScheduleStatus, RunStatusSensorDefinition, run_status_sensor, DagsterRunStatus, RunRequest
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN

# --- CONFIGURATION ---
MODEL_NAME = 'all-MiniLM-L6-v2' 

def get_db_conn():
    """Establishes a connection to Supabase using the Env Var"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is missing! Check your docker-compose.yml")
    return psycopg2.connect(db_url)

@asset
def article_vectors():
    """
    Step 1: The Translator
    Reads new articles (where embedding is NULL) and converts them to vector lists.
    """
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # 1. Fetch Work Queue
    # We LIMIT 100 to prevent crashing RAM on smaller servers
    query = """
        SELECT id, title, content_summary 
        FROM articles 
        WHERE embedding IS NULL
        LIMIT 100; 
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No new articles to vectorize.")
        conn.close()
        return Output(0, metadata={"status": "Skipped - No Work"})

    # 2. Load AI Model
    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # 3. Prepare Text
    texts_to_embed = [f"{r[1]} {r[2] or ''}" for r in rows]
    
    # 4. Generate Embeddings
    print(f"Generating vectors for {len(rows)} articles...")
    embeddings = model.encode(texts_to_embed)

    # 5. Save Back to DB
    updates = []
    for i, row in enumerate(rows):
        article_id = row[0]
        # Convert numpy array to simple python list
        vector_list = embeddings[i].tolist() 
        updates.append((vector_list, article_id))

    # FIX: Use executemany instead of execute_values for UPDATEs
    print(f"Saving {len(updates)} embeddings to DB...")
    cursor.executemany(
        "UPDATE articles SET embedding = %s WHERE id = %s",
        updates
    )
    conn.commit()
    conn.close()
    
    return Output(len(updates), metadata={"New Vectors": len(updates)})


@asset(deps=[article_vectors])
def topic_clusters():
    """
    Step 2: The Grouper
    Looks at all articles from the last 24 hours and groups similar ones.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    # 1. Fetch Recent Data
    cursor.execute("""
        SELECT id, embedding 
        FROM articles 
        WHERE inserted_at > NOW() - INTERVAL '24 hours'
        AND embedding IS NOT NULL;
    """)
    rows = cursor.fetchall()
    
    if len(rows) < 2:
        conn.close()
        return Output(0, metadata={"status": "Not enough data to cluster"})

    # 2. Prepare Data for DBSCAN
    article_ids = [r[0] for r in rows]
    
    # Handle pgvector format (string or list)
    vectors = []
    for r in rows:
        raw_vec = r[1]
        if isinstance(raw_vec, str):
            vectors.append(eval(raw_vec))
        else:
            vectors.append(raw_vec)
            
    X = np.array(vectors)

    # 3. Run Clustering (DBSCAN)
    print(f"Clustering {len(X)} articles...")
    clustering = DBSCAN(eps=0.4, min_samples=2, metric='cosine').fit(X)
    labels = clustering.labels_ 

    # 4. Map Clusters to UUIDs
    unique_labels = set(labels)
    label_to_uuid = {lbl: str(uuid.uuid4()) for lbl in unique_labels if lbl != -1}

    updates = []
    for i, label in enumerate(labels):
        if label == -1: 
            # -1 means "Noise" (Unique article, no group). Set to NULL.
            updates.append((None, article_ids[i]))
        else:
            updates.append((label_to_uuid[label], article_ids[i]))

    # 5. Write Updates
    # FIX: Use executemany here too
    print(f"Updating clusters for {len(updates)} articles...")
    cursor.executemany(
        "UPDATE articles SET cluster_id = %s WHERE id = %s",
        updates
    )
    conn.commit()
    conn.close()

    n_clusters = len(label_to_uuid)
    n_grouped = len([l for l in labels if l != -1])
    
    return Output(
        n_clusters, 
        metadata={
            "Stories Found": n_clusters, 
            "Articles Grouped": n_grouped,
            "Noise (Ignored)": len(labels) - n_grouped
        }
    )

# --- JOB DEFINITIONS ---
process_job = define_asset_job(name="process_news_job", selection=["article_vectors", "topic_clusters"])

defs = Definitions(
    assets=[article_vectors, topic_clusters],
    jobs=[process_job],
    sensors=[trigger_processing_on_ingestion_success]
)