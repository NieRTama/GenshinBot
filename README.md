# GenshinBot

原神プレイヤー向けのDiscord Botです。
以下の3つの機能を1つのBotにまとめています。

---

## できること

### 1. 聖遺物スコア計算

コマンド: `/score`

聖遺物のスクリーンショットを最大5枚送ると、OCRで自動読み取りしてスコアを計算します。

**パラメータ**

| パラメータ | 説明 |
|-----------|------|
| `image1`〜`image5` | 聖遺物の画像（1枚必須・最大5枚） |
| `mode` | 評価モード（省略時は会心重視） |

**評価モード**

| モード | 計算式 |
|--------|--------|
| 会心重視（デフォルト） | 会心率 × 2 ＋ 会心ダメージ |
| 攻撃重視 | 会心スコア ＋ 攻撃力% × 1.5 |
| 元素熟知重視 | 会心スコア ＋ 元素熟知 ÷ 4 |
| 元素チャージ重視 | 会心スコア ＋ チャージ効率 × 1.2 |
| 防御重視 | 会心スコア ＋ 防御力% × 1.5 |

**読み取る項目**

- 会心率 / 会心ダメージ / 攻撃力% / 防御力% / 元素チャージ効率 / 元素熟知

**総合ランク（複数枚の合計スコアで判定）**

| ランク | スコア |
|--------|--------|
| SS | 220以上 |
| S | 200以上 |
| A | 180以上 |
| B | 150以上 |
| C | 150未満 |

結果は部位（花 → 羽 → 時計 → 杯 → 冠）順にソートされ、サムネイルコラージュ画像付きのEmbedで返信されます。

---

### 2. イベント自動通知

[原神wiki（wikiwiki）](https://wikiwiki.jp/genshinwiki/%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%E4%B8%80%E8%A6%A7)の「開催中イベント（期間限定）」を**3時間ごと**に自動監視します。

**自動通知の種類**

| タイミング | 内容 |
|-----------|------|
| 新規イベント検出時 | 🎉 イベント名・開催期間をEmbedで通知 |
| 終了3日前 | ⏰ イベント名・終了日時をEmbedで通知（1回のみ） |
| 終了後 | 自動でDBから削除（再通知なし） |

- 取得済みのイベントは `data/events.json` に保存
- すでに終了したイベントはスクレイピング時点で除外

**月次リマインダー（毎日21時に自動送信）**

| 送信日 | 内容 |
|--------|------|
| 毎月1日 | チケット交換可能 |
| 毎月14日 | 螺旋の切替が近いです |
| 毎月30日 | シアターの切替が近いです |

**@everyone 監視**

指定チャンネルで `@everyone` が送信されると自動返信します。

| 条件 | 返信内容 |
|------|---------|
| 月曜日 | 週ボスあり。 |
| 開催中イベントがある場合 | イベント名と終了日を全件返信 |

---

### 3. ギフトコード自動検出

GameWithの原神ページを**3時間ごと**に監視し、新しいギフトコードを発見したら自動でDiscordに通知します。

- **検出方法**: リンク・タグ・正規表現の3段階で抽出
- **重複通知防止**: 一度通知したコードは `data/known_codes.json` に記録し、再通知しない
- **通知内容**: コード・HoyoVerse公式受け取りリンクを `@here` 付きで投稿

---

## スラッシュコマンド一覧

| コマンド | 説明 |
|---------|------|
| `/score` | 聖遺物スコア計算 |
| `/ping` | 動作確認（Pong!と返信） |

---

## セットアップ

### 必要なもの

- Python 3.10 以上
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)（日本語パック含む）
  - インストール先は `C:\Program Files\Tesseract-OCR\` のままにする
  - インストール時に「Japanese」を追加選択する
- Discord Bot トークン（[Discord Developer Portal](https://discord.com/developers/applications) で取得）

### インストール手順

```bash
# リポジトリを取得
git clone https://github.com/NieRTama/GenshinBot.git
cd GenshinBot

# パッケージをインストール
pip install -r requirements.txt
```

### .env の設定

`.env.example` をコピーして `.env` を作成し、3つの値を入力します。

```
DISCORD_TOKEN=BotのトークンをここにペーストBotのトークン

# @everyone監視・月次リマインダー・イベント通知を送るチャンネルのID
NOTIFY_CHANNEL_ID=チャンネルIDを数字で

# ギフトコード通知を送るチャンネルのID（NOTIFY_CHANNEL_IDと同じでも可）
GIFTCODE_CHANNEL_ID=チャンネルIDを数字で
```

**チャンネルIDの取得方法**
Discordの 設定 → 詳細設定 → **開発者モード** をONにしてから、チャンネルを右クリック →「IDをコピー」

### Discord Developer Portal の設定

- **Bot権限**: `Send Messages` / `Embed Links` / `Attach Files` / `Read Message History`
- **Privileged Intents**: 不要（すべてデフォルトIntentのみで動作）

### 起動

```bash
python bot.py
```

Ctrl+C で停止できます。

---

## ファイル構成

```
GenshinBot/
├── bot.py                      # 起動エントリーポイント
├── .env                        # 環境変数（Gitで管理しない）
├── .env.example                # 設定ファイルのテンプレート
├── requirements.txt            # 依存パッケージ
├── cogs/
│   ├── artifact.py             # /score・/ping（聖遺物スコア計算）
│   ├── notify.py               # イベント自動通知・月次リマインダー・@everyone監視
│   └── giftcode.py             # ギフトコード自動検出
├── utils/
│   ├── artifact_parser.py      # OCRテキストから統計値を抽出
│   └── score_calculator.py     # モード別スコア計算
└── data/                       # 実行時に自動生成
    ├── events.json             # 検出済みイベント（終了後自動削除）
    └── known_codes.json        # 検出済みギフトコード一覧
```

---

## 注意事項

- 聖遺物スコア計算は**日本語クライアントのスクリーンショットのみ**対応
- イベント情報はwikiwikiの更新タイミングに依存する
- ギフトコード検出はGameWithの掲載タイミングに依存する
- `data/events.json` を削除すると、現在開催中のイベントがすべて再通知される
- `data/known_codes.json` を削除すると、既存のコードがすべて再通知される
