# 第6章《数据脱敏与安全合规》代码落地包

> 配套公众号文章：【具身智能全栈工程·第6章】一条人脸毁掉整个开源计划
> 落地目标：文本 PII 扫描打码、区域模糊示意、双检测器审计与脱敏证书（合规留痕）。

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| `demo_privacy_redact.py` | L1 | 手机/身份证/邮箱正则定位替换 + 灰度矩阵区域盒式模糊 + 生成 L2 样例 |
| `engineering_privacy_scan.py` | L2 | 递归扫描结构化记录全部字符串、替换留痕、pii_report 分级、残留校验退出码 |
| `advanced_double_scan_audit.py` | L3 | 检测器A(正则)+检测器B(数字串启发)双检、A/B不一致人工清单、稳定打码、脱敏证书 checksum |

## 2. 环境

Python 3.9+，零第三方依赖（实测 3.13.3）。真实图像脱敏建议加 OpenCV/Pillow（改造指南说明）。

## 3. 快速运行

```bash
cd 第6章-数据脱敏与安全合规
python demo_privacy_redact.py --out sample_records.json
python engineering_privacy_scan.py --input sample_records.json --out-dir out
python advanced_double_scan_audit.py --input sample_records.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：
```text
脱敏: 操作者 alice 电话 [mobile_cn]，身份证 [id_cn]，邮箱 [email] 已授权
命中: [id_cn, mobile_cn, email]
区域打码: 框内首行变化像素 10/10
```

L2：
```text
扫描完成: 命中 3 处 (P0=3, 残留=0)
  [mobile_cn] root[0].operator_note: 13912345678 -> [已替换]
  [id_cn] root[0].file_name: 110101199003071234 -> [已替换]
风险: clean-after-sanitize   （退出码 0 = 脱敏后零残留）
```

L3（演示"宽召回检测器抓漏网"）：
```text
双检审计: 命中 4 处, A/B不一致 1 处
  待人工: root[0].log_ref B检出A未检出
结论: release-blocked | 证书 checksum: 4e44f5519a8ea100
```

## 5. 参数白皮书

| 参数 | 默认/工程值 | 适配 | 禁忌 |
| --- | --- | --- | --- |
| 身份证正则 | 18位含校验位、前后非数字 | 中文证件 | 港澳/护照需另配 |
| 手机号正则 | 1[3-9] 开头 11 位、前后非数字 | 大陆手机 | 座机/海外号码另配 |
| 邮箱正则 | 标准邮箱 | 通用 | 中文域名需扩展 |
| RISK 分级 | id/mobile=P0, email=P1 | 默认 | 按合规要求调整 |
| 双检不一致 | 任何 disagreement → release-blocked | 开源发布前 | 不允许跳过人工 |

## 6. Top5 踩坑与修复

| 现象 | 根因 | 修复 |
| --- | --- | --- |
| 1. 身份证被手机号正则截断误标 | 正则无边界且手机号先匹配 | ID 优先 + 前后加 (?<!\d)(?!\d)（本包已修） |
| 2. 打了码还有残留 | 只扫了部分字段 | L2 递归全字段扫描 + 残留=0 校验 |
| 3. 漏检拼接/长数字 | 单检测器盲区 | L3 双检 + disagreement 人工清单 |
| 4. 发布后追责无据 | 无处理记录 | L3 生成 checksum 脱敏证书归档 |
| 5. 文件名里的 ID 没扫到 | 只扫文本字段 | 递归扫描包含文件名（file_name 已覆盖） |

## 7. 改造指南

- 真实图像：把 demo 的矩阵模糊换成 OpenCV/Pillow 的 `GaussianBlur`/遮盖，框来自检测器输出；
- 更多 PII：向 PATTERNS/A_PATTERNS 添加 车牌/护照/坐标 等规则；
- 合规链：L3 证书 + 采集授权清单（第6章）一并归档，开源前人工复核 disagreement。

## 8. 进阶方向

接入数据流水线作为发布门禁 stage；把"检测器版本+阈值+抽验结果"写进数据集卡，实现"脱敏证书随数据集版本走"。
