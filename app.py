from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from profiler import OSINTProfiler
import uvicorn

app = FastAPI(title="OSINT Profiler API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

profiler = OSINTProfiler()

@app.get("/")
async def root():
    return {"message": "OSINT Profiler API is running"}

@app.get("/search")
async def search(first: str = Query(...), last: str = Query(...)):
    """
    Search for a person by first and last name.
    """
    results = await profiler.scan(first, last)
    # Generate search links for full name as well
    search_links = [
        {"platform": "Google", "url": f"https://www.google.com/search?q=%22{first}+{last}%22"},
        {"platform": "LinkedIn", "url": f"https://www.linkedin.com/search/results/all/?keywords={first}%20{last}"},
        {"platform": "Facebook", "url": f"https://www.facebook.com/search/people/?q={first}%20{last}"}
    ]
    return {
        "query": {"first": first, "last": last},
        "profiles": results,
        "deep_links": search_links
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
