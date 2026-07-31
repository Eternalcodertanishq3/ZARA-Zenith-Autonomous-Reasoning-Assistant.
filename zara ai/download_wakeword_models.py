try:
    from openwakeword.utils import download_models
    print("Downloading all models...")
    download_models(target_directory="C:\\Personal Projects\\ZARA_AI\\venv\\Lib\\site-packages\\openwakeword\\resources\\models")
    print("Download complete.")
except ImportError:
    print("Could not import download_models from openwakeword.utils")
except Exception as e:
    print(f"Error downloading models: {e}")
