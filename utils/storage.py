"""
Storage utility for NEXUS Platform
Handles file operations and data persistence
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import pickle


class Storage:
    """Storage manager for NEXUS data"""

    def __init__(self, base_path: str = "data"):
        """Initialize storage with base path"""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save_json(self, filename: str, data: Any, subdir: str = "") -> bool:
        """Save data as JSON"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False

    def load_json(self, filename: str, subdir: str = "") -> Optional[Any]:
        """Load JSON data"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
        return None

    def save_pickle(self, filename: str, data: Any, subdir: str = "") -> bool:
        """Save data as pickle"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving pickle: {e}")
            return False

    def load_pickle(self, filename: str, subdir: str = "") -> Optional[Any]:
        """Load pickle data"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading pickle: {e}")
        return None

    def list_files(self, subdir: str = "", extension: str = "") -> List[str]:
        """List files in directory"""
        try:
            path = os.path.join(self.base_path, subdir)
            if os.path.exists(path):
                files = os.listdir(path)
                if extension:
                    files = [f for f in files if f.endswith(extension)]
                return sorted(files)
        except Exception as e:
            print(f"Error listing files: {e}")
        return []

    def delete_file(self, filename: str, subdir: str = "") -> bool:
        """Delete a file"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False

    def save_text(self, filename: str, content: str, subdir: str = "") -> bool:
        """Save text content"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving text: {e}")
            return False

    def load_text(self, filename: str, subdir: str = "") -> Optional[str]:
        """Load text content"""
        try:
            path = os.path.join(self.base_path, subdir, filename)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading text: {e}")
        return None


# Global storage instance
storage = Storage()
