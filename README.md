# GenshinBot

原神プレイヤー向けのDiscord Botです。
以下の3つの機能を1つのBotにまとめています。

---

## 機能一覧

### 1. 聖遺物スコア計算（/score）

聖遺物のスクリーンショットを送ると、OCRで自動読み取りしてスコアを計算します。

**使い方**
```
/score image1:<画像> [image2〜image5] [mode:<評価モード>]
```

- 画像は最大5枚まで同時に処理できます
- 評価モードは以下から選択できます

| モード | 内容 |
|--------|------|
| 会心重視（デフォルト） | 会心率 × 2 ＋ 会心ダメージ |
| 攻撃重視 | 会心スコア ＋ 攻撃力% × 1.5 |
| 元素熟知重視 | 会心スコア ＋ 元素熟知 ÷ 4 |
| 元素チャージ重視 | 会心スコア ＋ チャージ効率 × 1.2 |
| 防御重視 | 会心スコア ＋ 防御力% × 1.5 |

**総合ランク**

| ランク | スコア |
|--------|--------|
| SS | 220以上 |
| S | 200以上 |
| A | 180以上 |
| B | 150以上 |
| C | 150未満 |

結果は部位（花・羽・時計・杯・冠）ごとにソートされ、コラージュ画像付きのEmbedで返信されます。

---

### 2. 定期通知・イベント管理

#### 月次リマインダー（自動・毎日21時）

特定の日付に自動でチャンネルへ通知します。

| 日付 | 通知内容 |
|------|----------|
| 毎月1日 | チケット交換可能 |
| 毎月14日 | 螺旋の切替が近いです |
| 毎月30日 | シアターの切替が近いです |

#### @everyone 監視（自動）

指定チャンネルで `@everyone` が送信されたとき、状況に応じて自動返信します。

- **月曜日**の場合 → `週ボスあり。` と返信
- **イベント期間中**の場合 → 登録されているイベント情報を返信

#### イベント登録（/event）

```
/event start:<開始日> end:<終了日> content:<内容>
```

- 日付は `YYYY/MM/DD` 形式で入力
- 登録したイベントは `data/event.json` に保存され、Bot再起動後も維持されます

---

### 3. ギフトコード自動検出

GameWithの原神ページを定期的に監視し、新しいギフトコードを発見したら自動でDiscordに通知します。

- **チェック頻度**: 3時間ごと
- **検出方法**: リンク・タグ・正規表現の3段階で抽出
- **重複通知防止**: 一度通知したコードは `data/known_codes.json` に記録し、再通知しません
- **通知内容**: コード・受け取りリンク（HoyoVerse公式）を `@here` メンション付きで投稿

---

## セットアップ

### 必要なもの

- Python 3.10 以上
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)（日本語パック含む）
  - インストール先: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Discord Bot トークン（[Discord Developer Portal](https://discord.com/developers/applications) で取得）

### インストール

```bash
pip install -r requirements.txt
```

### 設定

`.env.example` をコピーして `.env` を作成し、各値を入力してください。

```
DISCORD_TOKEN=your_discord_bot_token_here

# @everyone監視・月次リマインダーを送るチャンネルID
NOTIFY_CHANNEL_ID=your_channel_id_here

# ギフトコード通知を送るチャンネルID（NOTIFY_CHANNEL_IDと同じでも可）
GIFTCODE_CHANNEL_ID=your_channel_id_here
```

### Discord Developer Portal の設定

[Developer Portal](https://discord.com/developers/applications) でBotの以下の設定が必要です。

- **Bot権限**: `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`
- **Privileged Intents**: 不要（`message_content` は使用していません）

### 起動

```bash
python bot.py
```

---

## ファイル構成

```
GenshinBot/
├── bot.py                      # 起動エントリーポイント
├── .env                        # 環境変数（Gitで管理しない）
├── .env.example                # 設定ファイルのテンプレート
├── requirements.txt
├── cogs/
│   ├── artifact.py             # 聖遺物スコア計算
│   ├── notify.py               # 定期通知・イベント管理
│   └── giftcode.py             # ギフトコード自動検出
├── utils/
│   ├── artifact_parser.py      # OCRテキストから統計値を抽出
│   └── score_calculator.py     # モード別スコア計算
└── data/                       # 実行時に自動生成
    ├── event.json              # 登録イベント情報
    └── known_codes.json        # 検出済みギフトコード一覧
```

---

## 注意事項

- 聖遺物スコア計算は日本語クライアントのスクリーンショットのみ対応しています
- ギフトコード検出はGameWithの掲載タイミングに依存します
- `data/known_codes.json` を削除すると、既存のコードがすべて再通知されます
