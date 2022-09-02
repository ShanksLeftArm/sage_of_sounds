
class Song():
    def __init__(self, song_data: dict) -> None:
        self.url = song_data['webpage_url']
        self.title = song_data['title']