#!/usr/bin/env python3
"""
Script to run database migrations for email verification feature.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase Connection
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_migration():
    """Run the email verification migration."""
    print("Starting email verification migration...")
    
    try:
        # Read migration SQL
        with open('add_email_verification.sql', 'r') as f:
            migration_sql = f.read()
        
        print("Migration SQL:")
        print(migration_sql)
        print("\nExecuting migration...")
        
        # Execute each SQL statement separately
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            print(f"\nExecuting statement {i}...")
            print(statement[:100] + "..." if len(statement) > 100 else statement)
            
            try:
                # Use Supabase's RPC to execute raw SQL
                result = supabase.rpc('exec_sql', {'query': statement}).execute()
                print(f"✓ Statement {i} executed successfully")
            except Exception as e:
                # If RPC doesn't exist, try alternative approach
                print(f"Note: {str(e)}")
                print("Alternative: Please run the SQL migration manually in Supabase SQL Editor")
                print("\nSQL to run:")
                print("="*60)
                print(migration_sql)
                print("="*60)
                return False
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("\nPlease run the following SQL manually in Supabase SQL Editor:")
        print("="*60)
        with open('add_email_verification.sql', 'r') as f:
            print(f.read())
        print("="*60)
        return False

if __name__ == "__main__":
    run_migration()
