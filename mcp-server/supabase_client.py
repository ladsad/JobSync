from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    try:
        # Perform a simple read query to check the connection
        response = supabase.table('tasks').select('id').limit(1).execute()
        print("Successfully connected to Supabase.")
        return True
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    test_connection()
