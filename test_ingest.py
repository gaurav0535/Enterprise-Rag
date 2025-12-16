import requests
import sys

def ingest_file(file_path, api_url="http://localhost:8000/ingest"):
    """Make API call to ingest a file"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'text/plain')}
            response = requests.post(api_url, files=files)
            
        if response.status_code == 200:
            print("✅ Success! File ingested successfully.")
            print(f"Response: {response.json()}")
            return response.json()
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("Make sure the server is running with: uvicorn ingestion_service.app:app --reload")
        return None
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    file_path = "test.txt"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    print(f"Uploading file: {file_path}")
    ingest_file(file_path)

