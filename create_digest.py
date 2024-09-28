from telethon.sync import TelegramClient
from collections import Counter
from  datetime import datetime, timezone
from functools import reduce
import yaml
import os
from telethon.tl.types import MessageEntityTextUrl

APPID = os.getenv("APPID")
APPHASH = os.getenv("APPHASH")

with open('channels.yaml', 'r') as file:
    doc = list(yaml.safe_load_all(file))[0]

first_date = datetime(2024, 9, 1).replace(tzinfo=timezone.utc)
last_date = datetime(2024, 10, 1).replace(tzinfo=timezone.utc)

TIME_INTERVAL = "2409"

#http://www.thamnos.de/misc/look-up-bibliographical-information-from-an-arxiv-id/


channels = doc["DS"]
channels_tl = doc["TL"]

def extract_link(w):
    if w.startswith("https://arxiv.org"):
        return w
    elif "](" in w:
        return w.split("](")[1].split(")")[0]
    elif "(" in w:
        return w.split("(")[1].split(")")[0]
    else:
        raise(Exception(f"Could not parse link {w}"))
    
class MessageCounter():
    def __init__(self) -> None:
        self.cnt = Counter()
        self.props = {}

    def insert(self, art_id, reactions_count, chan, message_date, message_id):
        self.cnt[art_id] += reactions_count
        if not art_id in self.props:
            self.props[art_id] = {"chan": chan, "date": message_date, "id": message_id}
        else:
            if message.date < self.props[art_id]["date"]:
                self.props[art_id] = {"chan": chan, "date": message.date, "id": message_id} 
    def get_top_posts(self, n):
        posts = self.cnt.most_common(n)
        out_posts = []
        for art_id, reactions_count in posts:
            art_link = "https://arxiv.org/abs/" + art_id
            chan = self.props[art_id]["chan"]
            msg_id = self.props[art_id]["id"]
            msg_link = "/".join(["https://t.me", chan, str(msg_id)])
            out_posts.append((art_link, chan, msg_link, reactions_count))
        return out_posts


mc = MessageCounter()
with TelegramClient("anon", APPID, APPHASH) as client:
    for chan in channels:
        for message in client.iter_messages(chan):
            if message.date < first_date:
                break
            if message.date > last_date:
                continue
            if not message.text:
                continue
            try:
                reactions_count = reduce(lambda x, y: x + y.count, message.reactions.results, 0)
            except Exception as e:
                print(e)
                reactions_count = 0
            for url_entity, inner_text in message.get_entities_text(MessageEntityTextUrl):
                url = url_entity.url
                if "https://arxiv.org" in url:
                    art_id = url.split("/")[-1]
                    if TIME_INTERVAL in art_id:
                        print(chan, art_id, reactions_count)
                        mc.insert(art_id=art_id, reactions_count=reactions_count, chan=chan, message_date=message.date, message_id = message.id)
                

ymc = MessageCounter()
with TelegramClient("anon", APPID, APPHASH) as client:
    for chan in channels_tl:
        for message in client.iter_messages(chan):
            if message.date < first_date:
                break
            if message.date > last_date:
                continue
            if not message.text:
                continue
            try:
                reactions_count = reduce(lambda x, y: x + y.count, message.reactions.results, 0)
            except Exception as e:
                print(e)
                reactions_count = 0
            for url_entity, inner_text in message.get_entities_text(MessageEntityTextUrl):
                url = url_entity.url
                if url.startswith("https://youtu"):
                    ymc.insert(art_id=url, reactions_count=reactions_count, chan=chan, message_date=message.date, message_id = message.id)

                    
tp = mc.get_top_posts(10)
for p in tp:
    print(p)

tp = ymc.get_top_posts(10)
for p in tp:
    print(p)

#TODO: 
#3 most liked papers 
#3 most liked fresh papers 
#3 github repos
#3 videos for data science
#for each art/video/repo - title, link, first publisher, number of reactions, post link