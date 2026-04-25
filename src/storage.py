from collections import defaultdict


class EventStorage:
    def __init__(self):
        self.events = defaultdict(list)

    def add_event(self, event):
        self.events[event.topic].append(event)

    def get_events(self, topic=None):
        if topic:
            return [event.model_dump(mode="json") for event in self.events.get(topic, [])]
        return {
            topic_name: [event.model_dump(mode="json") for event in topic_events]
            for topic_name, topic_events in self.events.items()
        }