import sys
print("Python version:", sys.version)
print("Python path:", sys.path)

print("Attempting to import app...")
try:
    from app import app
    print("Successfully imported app")
except Exception as e:
    print(f"Failed to import app: {e}")
    raise

if __name__ == "__main__":
    print("Running app...")
    app.run()