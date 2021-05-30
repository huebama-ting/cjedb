import argparse
import ast
import json
import logging
import re
import sqlite3
import unicodedata
from typing import Optional

import requests
from google.protobuf import json_format

import cjedb_pb2

UPSTREAM_DATA_URL = 'https://gamewith-tool.s3-ap-northeast-1.amazonaws.com/uma-musume/uma_event_datas.js'
UPSTREAM_DATA_HEADER = 'const eventDatas = ['
UPSTREAM_DATA_FOOTER = '];'

EXCLUDED_EVENT_CHARA_NAMES = {'URA'}

EXCLUDED_EVENT_NAMES = {'追加の自主トレ', '夏合宿（2年目）にて', '夏合宿(2年目)にて', '初詣', '新年の抱負',
                        'お大事に！', '無茶は厳禁！',
                        'レース勝利！(1着)', 'レース入着(2~5着)', 'レース敗北(6着以下)',
                        'あんし～ん笹針師、参☆上'}

EVENT_NAME_SUFFIX_TO_REMOVE = {'（お出かけ2）', '（お出かけ3）'}

PER_CHARA_EXCLUDE_EVENTS = {
    ('夏合宿(3年目)終了', 1007),  # ゴルシ, wrong event name, but no one else has this choice, and the choice does nothing
}

PERMITTED_DUPLICATED_EVENTS = {
    ('上々の面構えッ！', None): {400001024, 400001037},
    ('アイツの存在', 1009): {501009115, 501009413},  # ダイワスカーレット
    ('宝塚記念の後に・キーワード②', 1007): {501007309, 501007310, 501007423, 501007424},  # ゴルドシープ
    ('岐', 1016): {501016121, 501016409},  # ナリタブライアン
}

KNOWN_OVERRIDES = {
    ('"女帝"vs."帝王"', 1003): '“女帝”vs.“帝王”',
    ('マルゼンスキー、「好き」を語る', 1004): 'マルゼンスキー、『好き』を語る',
    ('支えあいの秘訣', 1004): '支え合いの秘訣',
    ('えっアタシのバイト…やばすぎ？', 1007): 'えっアタシのバイト……ヤバすぎ？',
    ('挑め、”宿命”', 1008): '挑め、“宿命”',
    ('楽しめ！一番', 1009): '楽しめ！　1番！',
    ('もう１度、決意を', 1014): 'もう1度、決意を',
    ('"女帝"と"帝王"', 1018): '“女帝”と“帝王”',
    ('"女帝"と"皇帝"', 1018): '“女帝”と“皇帝”',
    ('目指せ！大人のちゃんこ鍋☆', 1024): '目指せ！　大人のちゃんこ鍋☆',
    ('この壁を超えてゆけ！', 1035): 'この壁を越えてゆけ！',
    ('ラスボスはスペ', 1052): 'ラスボスはスぺ',
    ('食い倒れ！七福神グルメめぐり', 1056): '食い倒れ！　七福神グルメめぐり',
    ('"覇王"として', 1015): '“覇王”として',
    ('レイニーパワフル', 1010): 'レイニー・パワフル！',
    ('大切な方と一緒にッ！', 1041): '大切な方と、一緒にッ！',
    ('かっくいいね！', 1052): 'かっくいぃね！',
    ('開運！ラッキーテレフォン', 1056): '開運！　ラッキーテレフォン',
    ('ピンチの後は…？', 1056): 'ピンチの後は……？',
    ('麗姿、瞳に焼き付いて', 1018): '麗姿、瞳に焼きついて',
    ('レイニーピックアップ', 1010): 'レイニー・ピックアップ！',
    ('全てはーーーのため', 1038): 'すべては――のため',
    ('You’re My Sunshine☆', 1024): 'You\'re My Sunshine☆',
    ('With My Whole Heart!', 1024): 'With My Whole Heart！',
    ('甦れ！ゴルシ印のソース焼きそば！', 1007): '甦れ！　ゴルシ印のソース焼きそば！',
    ('08:36/朝寝坊、やばっ', 1040): '08:36／朝寝坊、やばっ',
    ('ヒシアマ姐さん奮闘記～問題児編～', 1012): 'ヒシアマ姐さん奮闘記　～問題児編～',
    ('シチースポットを目指して', 1029): '“シチースポット”を目指して',
    ('信仰心と親切心が交わる時ーー', 1056): '信仰心と親切心が交わる時――',
    ('13:12/昼休み、気合い入れなきゃ', 1040): '13:12／昼休み、気合い入れなきゃ',
    ('ヒシアマ姐さん奮闘記～追い込み編～', 1012): 'ヒシアマ姐さん奮闘記　～追い込み編～',
    ('オゥ！トゥナイト・パーティー☆', 1010): 'オゥ！　トゥナイト・パーティー☆',
    ('"皇帝"の激励', 1017): '“皇帝”の激励',
    ('#lol #Party! #2nd', 1065): '#lol #Party!! #2nd',
}


def fetch_gw_upstream():
    c = requests.get(UPSTREAM_DATA_URL).text
    c = c[c.find(UPSTREAM_DATA_HEADER) + len(UPSTREAM_DATA_HEADER) + 1:c.find(UPSTREAM_DATA_FOOTER)]
    return ast.literal_eval('[' + c + ']')  # A bad hack because Python happens to accept this :(


def open_db(path: str) -> sqlite3.Cursor:
    connection = sqlite3.connect(path)
    return connection.cursor()


def read_chara_names(cursor: sqlite3.Cursor) -> dict[str, int]:
    cursor.execute("""SELECT "index", text FROM text_data
                      WHERE category=170""")  # Not 6 because of '桐生院葵'
    return {row[1]: row[0] for row in cursor.fetchall()}


def try_match_event(cursor: sqlite3.Cursor, event_name: str, chara_id: Optional[int]) -> list[int]:
    event_name = event_name.replace('･', '・').replace('~', '～')  # Currently no events use these 2 replaced chars
    for suffix in EVENT_NAME_SUFFIX_TO_REMOVE:
        event_name = event_name.removesuffix(suffix)

    t = (event_name, chara_id)
    if t in KNOWN_OVERRIDES:
        event_name = KNOWN_OVERRIDES[t]
        t = (event_name, chara_id)

    cursor.execute("""SELECT "index" FROM text_data
                      WHERE category=181 AND text=?""", [event_name])
    possible_story_ids = [row[0] for row in cursor.fetchall()]

    if len(possible_story_ids) == 0:
        cursor.execute("""SELECT "index", text FROM text_data
                          WHERE category=181 AND text LIKE ?""", ['%' + event_name + '%'])
        rows = cursor.fetchall()
        if len(rows) == 1:
            row = rows[0]
            if str(row[0]).startswith('50%d' % chara_id) or str(row[0]).startswith('80%d' % chara_id):
                pass  # Chara ID matches, assume it's safe.
            else:
                logging.warning("Fuzzily mapped %s for chara %s to %d %s" % (event_name, chara_id, row[0], row[1]))
            return [row[0]]

        logging.warning("Unknown event %s for chara %d" % t)
        return []

    if len(possible_story_ids) == 1:
        return possible_story_ids

    if event_name == 'ダンスレッスン':
        # Just special case this...
        story_id = int('50%d506' % chara_id)
        if story_id in possible_story_ids:
            return [story_id]

    if t in PERMITTED_DUPLICATED_EVENTS:
        if set(possible_story_ids) == PERMITTED_DUPLICATED_EVENTS[t]:
            return possible_story_ids

    logging.warning("More than 1 event for event_name: " + event_name)
    return []


def match_events(cursor: sqlite3.Cursor, gw_data):
    chara_names = read_chara_names(cursor)

    result = {}

    for row in gw_data:
        event_name = unicodedata.normalize('NFC', row['e'])

        event_type = row['c']  # c: chara, s: support card, m: scenario?
        if event_type not in {'c', 's', 'm'}:
            logging.error('Detected unknown event_type: %s' % row)

        event_chara_name = re.sub(r'\(.+\)', "", row['n'])  # remove things like `(新衣装)`
        if event_chara_name not in chara_names and event_chara_name not in EXCLUDED_EVENT_CHARA_NAMES:
            logging.warning('Detected unknown event_chara: %s' % row)
        chara_id = chara_names.get(event_chara_name)

        if event_name in EXCLUDED_EVENT_NAMES or (event_name, chara_id) in PER_CHARA_EXCLUDE_EVENTS:
            continue

        story_ids = try_match_event(cursor, event_name, chara_id)
        for story_id in story_ids:
            if story_id in result:
                # Because upstream uses separate entries for support cards R vs SR vs SSR.
                # For now there is no case where the choices are different than each other, so just ignore.
                pass
            result[story_id] = row

    return result


text_formatter = lambda text: text.replace('[br]', '\n').replace('<hr>', '\n')


def convert_to_proto(events: dict) -> cjedb_pb2.Database:
    db = cjedb_pb2.Database()
    for k, v in events.items():
        e = cjedb_pb2.Event()
        e.story_id = k
        for choice in v['choices']:
            c = cjedb_pb2.Event.Choice()
            c.title = choice['n']
            c.text = text_formatter(choice['t'])
            e.choices.append(c)
        db.events.append(e)
    return db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_path", default="master.mdb")
    parser.add_argument("--output", default="cjedb.json")
    args = parser.parse_args()

    gw_data = fetch_gw_upstream()
    cursor = open_db(args.db_path)

    events = match_events(cursor, gw_data)
    db = convert_to_proto(events)

    with open(args.output, 'w') as f:
        json.dump(json_format.MessageToDict(db), f, ensure_ascii=False)


if __name__ == '__main__':
    main()
