print("Entering __init__.py")
try:
    from .main import create_app
    print("Successfully imported create_app")
except Exception as e:
    print(f"Failed to import create_app: {e}")
    raise

print("Creating app...")
try:
    app = create_app()
    print("Successfully created app")
except Exception as e:
    print(f"Failed to create app: {e}")
    raise