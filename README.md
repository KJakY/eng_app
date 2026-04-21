# English Conversation Practice App

## 必要なもの

- Python 3.11以上
- [Ollama](https://ollama.com)
- [ffmpeg](https://ffmpeg.org)

## セットアップ

### 1. Ollamaのインストールとモデルのダウンロード

\```bash
# https://ollama.com からインストール後
ollama pull gemma3
\```

### 2. ffmpegのインストール

\```bash
winget install ffmpeg
\```

### 3. パッケージのインストール

\```bash
pip install -r requirements.txt
\```

### 4. 起動

\```bash
python gui.py
\```

## 使い方

1. 起動するとトピック選択ダイアログが表示される
2. 3候補から好きなトピックを選んで「このトピックで始める」
3. AIが英語で話しかけてくる（音声読み上げあり）
4. テキスト入力またはマイクボタン長押しで返答
5. 3回会話するとフィードバックが表示される
6. フィードバック後に「言いたかった日本語」を入力すると英語表現を提案

## 音声の変更

`voice.py` の `VOICE` を変更するだけで切り替えられます。

\```python
VOICE = "en-US-JennyNeural"   # アメリカ英語・女性
VOICE = "en-US-GuyNeural"     # アメリカ英語・男性
VOICE = "en-GB-SoniaNeural"   # イギリス英語・女性
VOICE = "en-AU-NatashaNeural" # オーストラリア英語・女性
\```

## トピックの変更

`topics.txt` を編集するだけで自由に追加・変更できます。