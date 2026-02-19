import os
import psycopg2
from dagster import asset, Output, Definitions, define_asset_job, RunStatusSensorDefinition, run_status_sensor, DagsterRunStatus, RunRequest
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter Configuration
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:3000", # Optional, for OpenRouter rankings
        "X-Title": "Dagster News ETL", # Optional
    }
)

# --- CONFIGURATION ---
def get_db_conn():
    """Establishes a connection to Supabase using the Env Var"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is missing! Check your docker-compose.yml")
    return psycopg2.connect(db_url)

def generate_summary(articles):
    """
    Generates a summary using Claude 3.5 Sonnet via OpenRouter.
    Input: List of (title, summary) tuples.
    Output: Single string summary.
    """
    if not articles:
        return "No articles to summarize."
    
    # Prepare the context
    context_text = "\n\n".join([f"Title: {title}\nContent: {content}" for title, content in articles])
    
    prompt = f"""
    You are a professional news editor. 
    Summarize the following articles into a single, cohesive paragraph (max 3 sentences).
    Focus on the core event and significant details.
    
    Articles:
    {context_text}
    """

    if not OPENROUTER_API_KEY:
        print("Warning: OPENROUTER_API_KEY not found. Falling back.")
        return "Summary (Fallback): " + " | ".join([a[0] for a in articles[:3]])

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3.7-sonnet:thinking",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Lower temperature for more factual summaries
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        # Fallback
        titles = [a[0] for a in articles[:3]]
        return f"Error Summarizing. Topics: {' | '.join(titles)}"

@asset
def new_cluster_summaries():
    """
    Finds clusters that don't have a summary yet, allows for LLM processing,
    and saves the result to the cluster_summaries table.
    """
    conn = get_db_conn()
    cursor = conn.cursor()

    # 1. Find clusters needing summaries
    # Logic: Get unique cluster_ids from articles 
    #        EXCEPT those already in cluster_summaries
    query = """
        SELECT DISTINCT a.cluster_id
        FROM articles a
        WHERE a.cluster_id IS NOT NULL
        EXCEPT
        SELECT cluster_id FROM cluster_summaries;
    """
    cursor.execute(query)
    cluster_ids = [row[0] for row in cursor.fetchall()]

    if not cluster_ids:
        print("No new clusters to summarize.")
        conn.close()
        return Output(0, metadata={"status": "No work"})

    print(f"Found {len(cluster_ids)} clusters to summarize.")

    # 2. Process each cluster
    new_summaries = []
    
    for c_id in cluster_ids:
        # Fetch articles for this cluster
        cursor.execute("SELECT title, content_summary FROM articles WHERE cluster_id = %s", (str(c_id),))
        articles = cursor.fetchall()
        
        if not articles:
            continue

        # Generate Summary
        summary_text = generate_summary(articles)
        new_summaries.append((str(c_id), summary_text))
    
    # 3. Save to DB
    print(f"Saving {len(new_summaries)} summaries...")
    cursor.executemany(
        "INSERT INTO cluster_summaries (cluster_id, summary_text) VALUES (%s, %s)",
        new_summaries
    )
    conn.commit()
    conn.close()

    return Output(len(new_summaries), metadata={"Generated Summaries": len(new_summaries)})

# --- JOB DEFINITIONS ---
summarize_job = define_asset_job(name="summarize_news_job", selection=["new_cluster_summaries"])

# --- SENSORS ---
@run_status_sensor(run_status=DagsterRunStatus.SUCCESS, monitor_all_code_locations=True, request_job=summarize_job)
def trigger_summarize_on_process_success(context):
    """
    Triggers the summarization job when the processing job succeeds.
    """
    if context.dagster_run.job_name == "process_news_job":
        yield RunRequest(job_name="summarize_news_job")

defs = Definitions(
    assets=[new_cluster_summaries],
    jobs=[summarize_job],
    sensors=[trigger_summarize_on_process_success]
)
