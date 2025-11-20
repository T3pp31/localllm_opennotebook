# localllm_opennotebook

Open Notebookを社内vLLMサーバーと連携して利用するためのDocker環境です。

## 概要

- Open Notebook（NotebookLMのオープンソース実装）を利用
- APIは社内のvLLMで起動してあるモデルを利用
- Docker Composeで簡単にセットアップ可能

## ディレクトリ構造

```
localllm_opennotebook/
├── docker/
│   ├── docker-compose.yaml    # Docker Compose設定
│   ├── .env                   # 環境変数（実際の値）
│   └── .env.example           # 環境変数テンプレート
├── config/
│   ├── __init__.py
│   └── settings.py            # 設定管理モジュール
├── tests/
│   ├── conftest.py            # pytest設定
│   ├── test_settings.py       # 設定テスト
│   ├── test_docker_config.py  # Docker設定テスト
│   └── test_vllm_connection.py # vLLM接続テスト
├── requirements.txt           # Python依存関係
└── README.md
```

## セットアップ

### 1. 環境変数の設定

`docker/.env`ファイルを編集し、vLLMサーバーの設定を行います：

```bash
# vLLMエンドポイント設定
OPENAI_API_BASE=http://host.docker.internal:8000/v1
OPENAI_API_KEY=dummy-key

# 使用するモデル
DEFAULT_CHAT_MODEL=gpt-oss-20b
DEFAULT_TRANSFORMATION_MODEL=gpt-oss-20b
DEFAULT_EMBEDDING_MODEL=gpt-oss-20b
```

### 2. Dockerコンテナの起動

```bash
cd docker

# コンテナを起動
docker compose up -d

# ログを確認
docker compose logs -f
```

### 3. アプリケーションにアクセス

ブラウザで http://localhost:8501 にアクセスします。

## 設定

### 環境変数一覧

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `APP_PORT` | アプリケーションポート | 8501 |
| `LOG_LEVEL` | ログレベル | INFO |
| `OPENAI_API_BASE` | vLLMエンドポイント | http://localhost:8000/v1 |
| `OPENAI_API_KEY` | APIキー | dummy-key |
| `DEFAULT_CHAT_MODEL` | チャットモデル | gpt-oss-20b |
| `SURREAL_ADDRESS` | SurrealDBアドレス | ws://surreal-db:8000 |
| `SURREAL_USER` | DBユーザー名 | root |
| `SURREAL_PASS` | DBパスワード | root |

### vLLMサーバーへの接続

Docker内からホストマシンで動作しているvLLMサーバーにアクセスするには、`host.docker.internal`を使用します：

```bash
OPENAI_API_BASE=http://host.docker.internal:8000/v1
```

別のサーバーにvLLMがある場合は、そのIPアドレスを指定してください：

```bash
OPENAI_API_BASE=http://192.168.1.100:8000/v1
```

## テスト

### テストの実行

```bash
# venv環境をアクティベート
source /root/vllm/myenv/bin/activate

# 全テストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ --cov=config --cov-report=term-missing
```

### テスト構成

- `test_settings.py`: 設定モジュールのテスト（43ケース）
- `test_docker_config.py`: Docker設定ファイルのテスト
- `test_vllm_connection.py`: vLLM接続テスト（モックおよび統合テスト）

## 開発

### Pythonからの設定利用

```python
from config.settings import get_settings

settings = get_settings()

# OpenAIクライアントの設定取得
config = settings.get_openai_client_config()
# {'base_url': 'http://...', 'api_key': '...'}
```

### コンテナの停止

```bash
cd docker
docker compose down

# データも含めて削除
docker compose down -v
```

## トラブルシューティング

### vLLMに接続できない

1. vLLMサーバーが起動しているか確認
2. `OPENAI_API_BASE`のURLが正しいか確認
3. Docker内から接続する場合は`host.docker.internal`を使用

### データベース接続エラー

1. SurrealDBコンテナが起動しているか確認: `docker compose ps`
2. ヘルスチェックを確認: `docker compose logs surreal-db`

## ライセンス

このプロジェクトは[Open Notebook](https://github.com/lfnovo/open-notebook)をベースにしています。
