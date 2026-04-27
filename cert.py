#!/usr/bin/env python3
"""AI评测存证系统 - 基于SM2数字签名的评测结果防篡改工具"""

import sys
import json
import time
import argparse
import hashlib
from pathlib import Path
from gmssl import sm2, func, sm3


def _new_crypt(pub='0' * 128, priv='0' * 64):
    return sm2.CryptSM2(public_key=pub, private_key=priv)


def keygen(args):
    dummy = _new_crypt()
    n = int(dummy.ecc_table['n'], 16)
    priv_int = int(func.random_hex(32), 16) % (n - 1) + 1
    priv = format(priv_int, '064x')
    pub = dummy._kg(priv_int, dummy.ecc_table['g'])

    priv_path = Path(args.out) / 'private.key'
    pub_path = Path(args.out) / 'public.key'
    Path(args.out).mkdir(parents=True, exist_ok=True)

    priv_path.write_text(priv)
    pub_path.write_text(pub)
    print(f"[OK] 密钥已生成")
    print(f"     私钥: {priv_path}")
    print(f"     公钥: {pub_path}")
    print(f"     公钥指纹: {sm3.sm3_hash(list(bytes.fromhex(pub)))[:16]}...")


def sign(args):
    priv = Path(args.key).read_text().strip()
    pub_path = Path(args.key).parent / 'public.key'
    pub = pub_path.read_text().strip() if pub_path.exists() else '0' * 128

    raw = json.loads(Path(args.input).read_text())

    payload = json.dumps(raw, ensure_ascii=False, sort_keys=True)
    payload_bytes = payload.encode()
    content_hash = sm3.sm3_hash(list(payload_bytes))

    crypt = _new_crypt(pub, priv)
    signature = crypt.sign_with_sm3(payload_bytes)

    cert = {
        "version": "1.0",
        "algorithm": "SM2withSM3",
        "timestamp": int(time.time()),
        "evaluator": args.evaluator or "anonymous",
        "content_hash_sm3": content_hash,
        "payload": raw,
        "signature": signature,
        "public_key_fingerprint": sm3.sm3_hash(list(bytes.fromhex(pub)))[:16]
    }

    out_path = Path(args.output) if args.output else Path(args.input).with_suffix('.cert.json')
    out_path.write_text(json.dumps(cert, ensure_ascii=False, indent=2))
    print(f"[OK] 存证生成成功: {out_path}")
    print(f"     内容哈希(SM3): {content_hash[:16]}...")
    print(f"     签名: {signature[:16]}...")
    print(f"     时间戳: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cert['timestamp']))}")


def verify(args):
    cert = json.loads(Path(args.cert).read_text())
    pub = Path(args.key).read_text().strip()

    payload = json.dumps(cert['payload'], ensure_ascii=False, sort_keys=True)
    payload_bytes = payload.encode()

    # 验证内容哈希
    actual_hash = sm3.sm3_hash(list(payload_bytes))
    hash_ok = actual_hash == cert['content_hash_sm3']

    # 验证SM2签名
    crypt = _new_crypt(pub)
    sig_ok = crypt.verify_with_sm3(cert['signature'], payload_bytes)

    print("=" * 50)
    print("AI评测存证验证报告")
    print("=" * 50)
    print(f"存证文件  : {args.cert}")
    print(f"算法      : {cert.get('algorithm', 'N/A')}")
    print(f"评测人    : {cert.get('evaluator', 'N/A')}")
    ts = cert.get('timestamp', 0)
    print(f"签署时间  : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}")
    print(f"内容完整性: {'✓ 通过' if hash_ok else '✗ 失败 - 内容已被篡改!'}")
    print(f"SM2签名   : {'✓ 通过' if sig_ok else '✗ 失败 - 签名无效!'}")
    print("=" * 50)

    if hash_ok and sig_ok:
        print("结论: 存证有效，评测结果未被篡改")
        return 0
    else:
        print("结论: 存证验证失败！")
        return 1


def report(args):
    cert = json.loads(Path(args.cert).read_text())
    print(json.dumps(cert, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='AI评测存证系统 - 基于SM2数字签名')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_keygen = sub.add_parser('keygen', help='生成SM2密钥对')
    p_keygen.add_argument('--out', default='.', help='输出目录 (默认: 当前目录)')

    p_sign = sub.add_parser('sign', help='对评测结果进行SM2签名存证')
    p_sign.add_argument('--input', required=True, help='评测结果JSON文件')
    p_sign.add_argument('--key', required=True, help='私钥文件路径')
    p_sign.add_argument('--evaluator', default='', help='评测人标识')
    p_sign.add_argument('--output', default='', help='存证输出路径')

    p_verify = sub.add_parser('verify', help='验证存证真实性')
    p_verify.add_argument('--cert', required=True, help='存证JSON文件')
    p_verify.add_argument('--key', required=True, help='公钥文件路径')

    p_report = sub.add_parser('report', help='查看存证详情')
    p_report.add_argument('--cert', required=True, help='存证JSON文件')

    args = parser.parse_args()
    cmds = {'keygen': keygen, 'sign': sign, 'verify': verify, 'report': report}
    result = cmds[args.cmd](args)
    sys.exit(result or 0)


if __name__ == '__main__':
    main()
