import json
from src.utils import load_json, save_json


class SongFilter:
    def __init__(self, file_name="tags.json"):
        self.file_name = file_name
        self.filters = load_json(self.file_name)

    def add_filter(self, tag, value=1):
        self.filters[tag] = value

    def get_filter(self, tag, new_tags):
        if tag not in self.filters:
            self.add_filter(tag)
            new_tags.append(tag)
        return self.filters[tag]

    def save_filters(self):
        sorted_filters = {k: self.filters[k] for k in sorted(self.filters)}
        save_json(self.file_name, sorted_filters)

    def is_song_allowed(self, tags):
        new_tags = []
        is_allowed = all(self.get_filter(tag, new_tags) for tag in tags)
        # if new_tags:
        #     print(f"New tags added: {', '.join(new_tags)}")
        self.save_filters()  # Save after filtering to include newly added tags
        return is_allowed
