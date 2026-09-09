# Remevahe｜存真

> 存下此刻，留住真实。

Remevahe 是一个极简的个人记忆记录原型。第一版只保留一个核心动作：写下此刻，并在当天时间线上回看。

## 当前版本

- 本地网页界面
- 文字记录
- 自动记录时间
- SQLite 本地持久化
- Today 时间线
- `/health` 健康检查接口

暂不包含 AI、照片、视频、账号、云同步和语义搜索。后续功能将在这个最小闭环稳定后逐步加入。

## 运行

```bash
python3 app.py
```

打开 <http://127.0.0.1:8000>。

数据保存在项目目录下的 `remevahe.db`，不会上传到云端。

## API

```text
GET  /health
GET  /api/notes
POST /api/notes  {"content":"今天完成了第一版原型"}
```
