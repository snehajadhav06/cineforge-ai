import os
import json
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")


class StorageService:
    def __init__(self, base_dir: str = GENERATED_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_project_dirs(self, project_id: str = "default"):
        project_path = os.path.join(self.base_dir, "projects", project_id)
        subdirs = {
            "root": project_path,
            "input": os.path.join(project_path, "input"),
            "images": os.path.join(project_path, "images"),
            "videos": os.path.join(project_path, "videos"),
            "thumbnails": os.path.join(project_path, "thumbnails"),
        }

        for path in subdirs.values():
            os.makedirs(path, exist_ok=True)

        metadata_file = os.path.join(project_path, "metadata.json")
        if not os.path.exists(metadata_file):
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump({
                    "project_id": project_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }, f, indent=2)

        return subdirs

    def save_project_metadata(self, project_id: str, data: dict):
        dirs = self.get_project_dirs(project_id)
        metadata_file = os.path.join(dirs["root"], "metadata.json")

        existing = {}
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass

        existing.update(data)
        existing["updated_at"] = datetime.utcnow().isoformat()

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)


storage_service = StorageService()
