import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = os.getenv('API_ENDPOINT')
API_KEY = os.getenv('AI_POWER_GRID_API_KEY')

# Debug print to check if API_BASE_URL is loaded correctly
print(f"API_BASE_URL: {API_BASE_URL}")

# Headers
HEADERS = {
    "accept": "application/json",
    "apikey": API_KEY,
    "Client-Agent": "PythonWorkerChecker:1.0:test",
    "Content-Type": "application/json"
}

def get_available_workers():
    """
    Fetch and display detailed information about available workers
    """
    if not API_BASE_URL:
        print("Error: API_ENDPOINT is not set in the environment variables.")
        return

    endpoint = f"{API_BASE_URL}/api/v2/workers"
    print(f"Attempting to access endpoint: {endpoint}")

    try:
        print("Fetching available workers...")
        response = requests.get(endpoint, headers=HEADERS)
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            workers_data = response.json()
            print("\n=== Available Workers ===")
            for index, worker in enumerate(workers_data, 1):
                print(f"\n[Worker {index}]")
                print(f"ID: {worker.get('id', 'N/A')}")
                print(f"Name: {worker.get('name', 'N/A')}")
                print(f"Type: {worker.get('type', 'N/A')}")
                print(f"Status: {'[M] Maintenance' if worker.get('maintenance_mode', False) else '[A] Active'}")
                print(f"Operation: {'[P] Paused' if worker.get('paused', False) else '[R] Running'}")
                
                print("Supported Models:")
                for model in worker.get('models', []):
                    print(f"  * {model}")
                
                print(f"Performance: {worker.get('performance', 'N/A')}")
                
                max_pixels = worker.get('max_pixels', 'N/A')
                if isinstance(max_pixels, int):
                    print(f"Max Pixels: {max_pixels:,}")
                else:
                    print(f"Max Pixels: {max_pixels}")
                
                if worker.get('megapixelsteps_per_second'):
                    print(f"Speed: {worker.get('megapixelsteps_per_second')} megapixelsteps/second")
                
                if worker.get('uptime'):
                    print(f"Uptime: {worker.get('uptime')} seconds")
                
                if worker.get('jobs_completed'):
                    print(f"Jobs Completed: {worker.get('jobs_completed')}")
                
                if worker.get('kudos'):
                    print(f"Kudos: {worker.get('kudos'):,}")
                
                print("-" * 40)
            
            print(f"\nTotal workers: {len(workers_data)}")
            
            # Calculate and display additional statistics
            active_workers = sum(1 for w in workers_data if not w.get('maintenance_mode') and not w.get('paused'))
            total_performance = sum(float(w.get('performance', '0').split()[0]) for w in workers_data if w.get('type') == 'image')
            
            print(f"Active workers: {active_workers}")
            print(f"Total performance: {total_performance:.2f} megapixelsteps per second")
            
        else:
            print(f"Error: API response status is {response.status_code}")
            print("Response:", json.dumps(response.json(), indent=2))
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching workers: {e}")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    get_available_workers()