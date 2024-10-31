from telethon.sync import TelegramClient
from collections import Counter
from  datetime import datetime, timezone
from functools import reduce
import yaml
import os
from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl

APPID = os.getenv("APPID")
APPHASH = os.getenv("APPHASH")

with open('channels.yaml', 'r') as file:
    doc = list(yaml.safe_load_all(file))[0]

start_date = datetime(2024, 10, 1).replace(tzinfo=timezone.utc)
end_date = datetime(2024, 11, 1).replace(tzinfo=timezone.utc)

TIME_INTERVAL = "2410"
SUMMARY_LEN = 500

#http://www.thamnos.de/misc/look-up-bibliographical-information-from-an-arxiv-id/


channels = doc["DS"]
channels_tl = doc["TL"]

def extract_links(message):
    links = []
    for url_entity, inner_text in message.get_entities_text(MessageEntityTextUrl):
        url = url_entity.url
        links.append(url)
        
    for url_entity, url in message.get_entities_text(MessageEntityUrl):
        links.append(url)
    return links
        
class MessageCounter():
    def __init__(self) -> None:
        self.cnt = Counter()
        self.props = {}

    def insert(self, art_id, reactions_count, chan, message_date, message_id, message_summary):
        self.cnt[art_id] += reactions_count
        if not art_id in self.props:
            self.props[art_id] = {"chan": chan, "date": message_date, "id": message_id, "message_summary": message_summary}
        else:
            if message.date < self.props[art_id]["date"]:
                self.props[art_id] = {"chan": chan, "date": message.date, "id": message_id, "message_summary": message_summary} 
    def get_top_posts(self, n):
        posts = self.cnt.most_common(None)
        out_posts = []
        seen_msgs = set()
        added = 0
        for art_id, reactions_count in posts:
            chan = self.props[art_id]["chan"]
            msg_id = self.props[art_id]["id"]
            msg_link = "/".join(["https://t.me", chan, str(msg_id)])
            msg_summary = self.props[art_id]["message_summary"]
            if msg_id not in seen_msgs:
                out_posts.append((art_id, chan, msg_link, reactions_count, msg_summary))
                seen_msgs.add(msg_id)
                added += 1
                if added >= n:
                    break
            
        return out_posts


mc = MessageCounter()
with TelegramClient("anon", APPID, APPHASH) as client:
    for chan in channels:
        for message in client.iter_messages(chan):
            if message.date < start_date:
                break
            if message.date > end_date:
                continue
            if not message.text:
                continue
            summary = message.text[:SUMMARY_LEN] + "..."
            try:
                reactions_count = reduce(lambda x, y: x + y.count, message.reactions.results, 0)
            except Exception as e:
                reactions_count = 0

            links = extract_links(message)
            for url in links:
                if "https://arxiv.org" in url:
                    art_id = url.split("/")[-1]
                    art_id = "https://arxiv.org/abs/" + art_id
                    if TIME_INTERVAL in art_id:
                        print(chan, art_id, reactions_count)
                        mc.insert(art_id=art_id, reactions_count=reactions_count, chan=chan, message_date=message.date, message_id = message.id, message_summary=summary)


ymc = MessageCounter()
with TelegramClient("anon", APPID, APPHASH) as client:
    for chan in channels_tl:
        for message in client.iter_messages(chan):
            if message.date < start_date:
                break
            if message.date > end_date:
                continue
            if not message.text:
                continue
            summary = message.text[:SUMMARY_LEN] + "..."
            try:
                reactions_count = reduce(lambda x, y: x + y.count, message.reactions.results, 0)
            except Exception as e:
                reactions_count = 0
            links = extract_links(message)
            for url in links:
                if url.startswith("https://youtu"):
                    ymc.insert(art_id=url, reactions_count=reactions_count, chan=chan, message_date=message.date, message_id = message.id, message_summary=summary)
        
tp = mc.get_top_posts(10)
for i, p in enumerate(tp, start =1):
    art_url, nick, post_url, n_reacts, summary = p
    print(f"{i}. {n_reacts} реакций: {nick} опубликовал пост {post_url} со ссылкой на статью {art_url}")
    print(summary)

tp = ymc.get_top_posts(10)
for i, p in enumerate(tp, start =1):
    art_url, nick, post_url, n_reacts, summary = p
    print(f"{i}. {n_reacts} реакций: {nick} опубликовал пост {post_url} со ссылкой на видео {art_url}")
    print(summary)
