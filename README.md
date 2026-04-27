# AI 评测存证系统

> 基于 SM2/SM3 国密算法的 AI 模型评测结果防篡改存证工具

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![国密算法](https://img.shields.io/badge/算法-SM2withSM3-orange.svg)]()

## 简介

随着 AI 模型评测的广泛应用，评测结果的真实性和不可篡改性变得日益重要。`ai-eval-cert` 提供了一套基于**国密 SM2 数字签名 + SM3 哈希**的存证方案，可对任意 AI 评测 JSON 数据进行签名存证，并支持随时验证存证的完整性。

**典型场景：**
- AI 模型准入评测结果存证（监管留档）
- 第三方评测机构出具可验证的评测报告
- 评测数据的链下完整性保护

## 工作原理

```
评测结果 JSON
     │
     ├─► SM3 计算内容哈希
     │
     └─► SM2 私钥签名
              │
              ▼
        存证文件 .cert.json
        ┌─────────────────────┐
        │ version             │
        │ algorithm           │
        │ timestamp           │
        │ evaluator           │
        │ content_hash_sm3    │
        │ payload (原始数据)  │
        │ signature           │
        │ public_key_fingerprint │
        └─────────────────────┘
```

验证时：重新计算哈希 + 用公钥验签，两者均通过才判定存证有效。

## 安装

```bash
git clone https://github.com/your-username/ai-eval-cert.git
cd ai-eval-cert
pip install -r requirements.txt
```

依赖：
- `gmssl >= 3.2.2`（国密算法 Python 实现）

## 使用方法

### 1. 生成密钥对

```bash
python cert.py keygen --out ./keys
```

输出：
```
[OK] 密钥已生成
     私钥: keys/private.key
     公钥: keys/public.key
     公钥指纹: 87806029d9072cee...
```

> **安全提示**：私钥文件需妥善保管，切勿提交到代码仓库。

### 2. 对评测结果签名存证

准备评测结果 JSON 文件（`eval.json`）：

```json
{
  "model": "your-model-name",
  "task": "text_classification",
  "dataset": "test_dataset_v1",
  "metrics": {
    "accuracy": 0.923,
    "f1": 0.918
  },
  "test_samples": 5000,
  "pass": true
}
```

执行签名：

```bash
python cert.py sign \
  --input eval.json \
  --key keys/private.key \
  --evaluator "评测机构名称"
```

输出：
```
[OK] 存证生成成功: eval.cert.json
     内容哈希(SM3): e330cd1cea27553e...
     签名: 45bbff97422625c4...
     时间戳: 2026-04-24 09:02:55
```

### 3. 验证存证

```bash
python cert.py verify \
  --cert eval.cert.json \
  --key keys/public.key
```

输出：
```
==================================================
AI评测存证验证报告
==================================================
存证文件  : eval.cert.json
算法      : SM2withSM3
评测人    : 评测机构名称
签署时间  : 2026-04-24 09:02:55
内容完整性: ✓ 通过
SM2签名   : ✓ 通过
==================================================
结论: 存证有效，评测结果未被篡改
```

### 4. 查看存证详情

```bash
python cert.py report --cert eval.cert.json
```

## 存证文件格式

```json
{
  "version": "1.0",
  "algorithm": "SM2withSM3",
  "timestamp": 1776992551,
  "evaluator": "评测机构名称",
  "content_hash_sm3": "e330cd1cea27553e...",
  "payload": { ...原始评测数据... },
  "signature": "45bbff97422625c4...",
  "public_key_fingerprint": "87806029d9072cee"
}
```

## 示例文件

`examples/` 目录包含：
- `sample_eval.json`：示例评测结果（GPT-4o 情感分析评测）
- `sample_eval.cert.json`：对应的签名存证文件

```bash
# 使用示例公钥验证示例存证
python cert.py verify \
  --cert examples/sample_eval.cert.json \
  --key keys/public.key
```

## 安全说明

- 签名算法：SM2withSM3（符合 GM/T 0009 标准）
- 私钥长度：256 bit
- 公钥指纹：SM3 哈希前 8 字节（用于快速识别密钥对）
- **私钥务必离线保存**，公钥可公开分发用于验证

## License

MIT
