# Raspberry Pi LED Illumination Controller

Raspberry Pi の GPIO（**GPIO 17 / 物理11番ピン**、2SC1815 トランジスタ等によるスイッチング回路経由）を使って LED イルミネーションを制御する Web アプリケーションとスケジュール実行スクリプトです。

スマートフォンのブラウザから以下の操作・設定を行えます。
- 手動での強制 ON / 強制 OFF
- 終日つけっぱなしモード（常時 ON）の切り替え
- 祝日・特別日（`YYYY-MM-DD` 単位、曜日設定より優先）の朝・夕 ON/OFF 時刻設定
- 曜日別（`mon`〜`sun`）の朝・夕 ON/OFF 時刻設定

---

## 構成ファイル

- `app.py`: スマホ向け Web UI および操作・設定保存 API を提供する Flask アプリケーション
- `check_schedule.py`: `cron` から毎分呼び出され、`schedule_config.json` に基づいて GPIO を制御するスクリプト
- `schedule_config.json`: Web UI から保存される設定ファイル（初回保存時に自動生成、`.gitignore` 対象）

---

## ハードウェアと安全上の注意

- 制御ピンは **GPIO 17（物理11番ピン）** に固定しています（別のピンを使う場合は `app.py` と `check_schedule.py` の `LED_PIN` を書き換えてください）。
- Raspberry Pi の GPIO 出力（3.3V、最大電流に制限あり）で高電流の LED テープライトや AC100V 機器を直接駆動しないでください。負荷に応じたトランジスタ（例: 2SC1815＋ベース抵抗）／MOSFET／リレー回路を介して接続してください。
- 配線や電源周りを触る際は、必ず電源を切ってから作業してください。

---

## セットアップ

### 1. リポジトリの取得と仮想環境の作成

システム側の GPIO ライブラリを仮想環境からも利用できるよう、`--system-site-packages` を付けて仮想環境を作成します。

```bash
git clone <your-repository-url> led_controller
cd led_controller

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install --upgrade pip
pip install flask gunicorn
```

Raspberry Pi OS / ハードウェア世代に応じて、`RPi.GPIO` または `rpi-lgpio` を導入してください（システムパッケージを使う場合は `apt` も利用できます）。

```bash
# 例: rpi-lgpio を使う場合
pip install rpi-lgpio
```

---

## 使い方

### 1. Web UI の起動（手動テスト）

```bash
/path/to/led_controller/.venv/bin/python /path/to/led_controller/app.py
```

同一ネットワーク内のスマートフォンや PC のブラウザから、以下の URL にアクセスします。

```text
http://<ラズパイのIPアドレス>:5000
```

Web UI から一度設定を保存すると、同じディレクトリに `schedule_config.json` が自動生成されます。

### 2. 自動スケジュール実行（`cron`）

`crontab -e` を開き、毎分 `check_schedule.py` を実行するよう追記します。

```cron
* * * * * /path/to/led_controller/.venv/bin/python /path/to/led_controller/check_schedule.py
```

### 3. `systemd` による常時起動（推奨）

端末を閉じても Web UI を維持したい場合は、`systemd` サービスとして登録します。

`/etc/systemd/system/led-controller.service` の作成例：

```ini
[Unit]
Description=LED Illumination Flask Controller
After=network.target

[Service]
Type=simple
User=<your-username>
WorkingDirectory=/path/to/led_controller
ExecStart=/path/to/led_controller/.venv/bin/gunicorn --workers 1 --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

反映と起動：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now led-controller.service
sudo systemctl status led-controller.service --no-pager
```
