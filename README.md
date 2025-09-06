# ICFP 2025 一把过解题程序

一个用来参加 **ICFP 2025**《绑定的名称》题目的一把过解题程序  
主程序：`solver.py`

---

只过了闪电赛前题目，后面没搞

## 环境要求
- Python 3.8+
- 依赖：`requests`
  ```bash
  pip install requests
  ```

---

## 快速上手

### 已有 team id
$env:TEAM_ID="你的邮箱 和 令牌之间有空格的 team id"
python solver.py --solve --problem secundus --n 32 --no-conformance
> 脚本会优先读取：`--id` ＞ 环境变量 `TEAM_ID` ＞ `team_id.txt`。

---

## 解题参数

**一条龙服务**
```bash
python solver.py --solve --problem <题目名> --n <估计房间数> --no-conformance
```

**稳妥带校验**
```bash
python solver.py --solve --problem <题目名> --n <估计房间数> --depth 3 --samples 200
```

**仅注册**
```bash
python solver.py --register --name "TeamName" --email "you@example.com" --pl python
```

**仅选题**
```bash
python solver.py --problem primus
```

---

## 参数说明
- `--problem`：题目名（如 `probatio`、`primus`、`secundus`、`quartus`…）。  
- `--n`：**估计**的房间数，只用于计算每次 `/explore` 的预算 `18 × n`。  
  建议设为真实房间数的 **1.5×～2×**，能减少回合次数。  
- `--no-conformance`：跳过随机一致性校验（更快但有风险）。  
- `--depth` / `--samples`：随机校验的深度和样本数（越大越稳）。  
- `--persist-cache`：把 membership 结果保存到 `cache.pkl`（中断后续跑更省请求）。  
- `--id` / `TEAM_ID`：形如 `"email token"` 的 team id（中间有空格）；或使用 `team_id.txt`。  

---

## 参数
```bash
# 小图 probatio
python solver.py --solve --problem probatio --n 3 --depth 2 --samples 80

# 中图 primus
python solver.py --solve --problem primus --n 12 --depth 3 --samples 200

# 较大 secundus（求快）
python solver.py --solve --problem secundus --n 32 --no-conformance

# quartus（稳妥）
python solver.py --solve --problem quartus --n 32 --depth 3 --samples 300
# 后面跑不动
```
> 想更少回合可把 `--n` 提到 **48** 或 **64**。

---

## 输出
- 探索进度：`/explore[轮次] p=<计划数> s=<步数> q=<累计queryCount>`  
- 学习结果：`Model: <状态数> states`  
- 校验结果：`Chk: PASS` 或 `FAIL/SKIP`  
- 提交结果：`Guess: True/False`  

---

## 故障排查
- **`no team id: --id / TEAM_ID / team_id.txt / --register`**  
  → 传 `--id`，或设置 `TEAM_ID`，或先 `--register`，或把 id 写入 `team_id.txt`。  
- **`/guess` 返回 False**  
  → 学习模型还没把状态完全区分出来。去掉 `--no-conformance`、加大 `--depth`/`--samples`、或提升 `--n` 再跑。  
- **需要续跑**  
  → 加 `--persist-cache`；再次运行会复用已查询结果。  

---
## 闪电环节归属（前 24 小时）
无。本代码库在比赛开始后 24 小时之后才开始编写；前 24 小时未产生任何代码。

`# AUTHORS: kiwi;lucas`

祝你上榜，Good luck!
