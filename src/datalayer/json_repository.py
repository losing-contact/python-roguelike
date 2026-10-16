import json
from dataclasses import asdict
from pathlib import Path

from datalayer.serializers import session_from_dict, session_to_dict
from domain.models.stats import RunStats


class JsonRepository:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.records_file = self.folder / "records.json"
        self.save_file = self.folder / "save.json"

    def save_session(self, session):
        """Записывает всю игровую сессию целиком (старое сохранение перезаписывается)."""
        self.folder.mkdir(parents=True, exist_ok=True)
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(session_to_dict(session), f)

    def load_session(self):
        """Возвращает сохранённую сессию или None, если сохранения нет или оно испорчено."""
        try:
            with open(self.save_file, encoding="utf-8") as f:
                return session_from_dict(json.load(f))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def delete_session(self):
        self.save_file.unlink(missing_ok=True)

    def add_record(self, stats):
        """Дописывает результат прохождения в таблицу рекордов."""
        records = self._read_records()
        records.append(asdict(stats))
        self.folder.mkdir(parents=True, exist_ok=True)
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def top_records(self, limit=10):
        """Лучшие прохождения: больше сокровищ выше, при равенстве - глубже уровень."""
        records = [RunStats(**data) for data in self._read_records()]
        records.sort(key=lambda r: (r.treasure, r.level_reached), reverse=True)
        return records[:limit]

    def _read_records(self):
        try:
            with open(self.records_file, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []  # файла нет или он испорчен: начинаем с пустой таблицы
