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

### 2. イベント自動通知

[原神wiki（wikiwiki）](https://wikiwiki.jp/genshinwiki/%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%E4%B8%80%E8%A6%A7)の「開催中イベント（期間限定）」を3時間ごとに自動監視し、以下を通知します。

| タイミング | 通知内容 |
|-----------|---------|
| 新規イベント検出時 | 🎉 イベント名と開催期間を通知 |
| 終了3日前 | ⏰ イベント名と終了日時を通知 |
| 終了後 | 自動でDBから削除（再通知なし） |

#### 月次リマインダー（自動・毎日21時）

| 日付 | 通知内容 |
|------|----------|
| 毎月1日 | チケット交換可能 |
| 毎月14日 | 螺旋の切替が近いです |
| 毎月30日 | シアターの切替が近いです |

#### @everyone 監視（自動）

指定チャンネルで `@everyone` が送信されたとき、状況に応じて自動返信します。

- **月曜日**の場合 → `週ボスあり。` と返信
- **開催中イベントがある場合** → 全イベントの名前と終了日を返信

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

# @everyone監視・月次リマインダー・イベント通知を送るチャンネルID
NOTIFY_CHANNEL_ID=your_channel_id_here

# ギフトコード通知を送るチャンネルID（NOTIFY_CHANNEL_IDと同じでも可）
GIFTCODE_CHANNEL_ID=your_channel_id_here
```

チャンネルIDはDiscordの 設定 → 詳細設定 → **開発者モード** をONにしてから、チャンネルを右クリック →「IDをコピー」で取得できます。

### Discord Developer Portal の設定

[Developer Portal](https://discord.com/developers/applications) でBotの以下の設定が必要です。

- **Bot権限**: `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`
- **Privileged Intents**: 不要（特権Intentは使用していません）

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
├── requirements.txt
├── cogs/
│   ├── artifact.py             # 聖遺物スコア計算（/score, /ping）
│   ├── notify.py               # イベント自動通知・月次リマインダー
│   └── giftcode.py             # ギフトコード自動検出
├── utils/
│   ├── artifact_parser.py      # OCRテキストから統計値を抽出
│   └── score_calculator.py     # モード別スコア計算
└── data/                       # 実行時に自動生成
    ├── events.json             # 検出済みイベント情報（終了後自動削除）
    └── known_codes.json        # 検出済みギフトコード一覧
```

---

## 注意事項

- 聖遺物スコア計算は日本語クライアントのスクリーンショットのみ対応しています
- イベント情報はwikiwikiの更新タイミングに依存します
- ギフトコード検出はGameWithの掲載タイミングに依存します
- `data/known_codes.json` を削除すると、既存のコードがすべて再通知されます
- `data/events.json` を削除すると、現在開催中のイベントがすべて再通知されます

---

## 更新履歴

### 2026-06-07
- 初回リリース（GenshinArtifactBot・notify-bot・Genshin-CodeBotを統合）
- イベント管理を手動コマンド（`/event`）から自動スクレイピングに変更
  - wikiwikiの「開催中イベント（期間限定）」を3時間ごとに自動監視
  - 新規イベント検出時・終了3日前に自動通知
  - 終了したイベントはDBから自動削除
  - スクレイピング時に終了済みイベントを除外
- `@everyone` 監視を複数イベント対応に更新
- Ctrl+C 停止時のエラー表示を修正
- 動作確認完了
