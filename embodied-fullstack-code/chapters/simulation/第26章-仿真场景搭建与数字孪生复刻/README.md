# 第26章《场景搭建与数字孪生复刻》代码落地包

> 配套文章：【具身智能全栈工程·第26章】别在"豆腐块场景"里练机器人

## 1. 三层文件

| 文件 | 层 | 能力 |
| --- | --- | --- |
| demo_asset_check.py | L1 | 资产五要素检查（mesh/mass/friction/collision/material）质量门禁 |
| engineering_scene_variants.py | L2 | 程序化变体生成：物体×位置×光照×桌面组合 + 种子/场景哈希可复现 |
| advanced_twin_check.py | L3 | 数字孪生一致性核对：真机 vs 仿真逐尺寸容差判定 |

## 2. 环境：Python 3.9+ 零依赖（实测 3.13.3）

## 3. 快速运行
```bash
python demo_asset_check.py
python engineering_scene_variants.py --n 10 --out out
python advanced_twin_check.py --make-sample sample
python advanced_twin_check.py --real sample/real.json --sim sample/sim.json --out-dir out
```

## 4. 标准运行结果（本机实测）

L1：mug_red/table OK，box_blue 缺 mesh/collision/material 被拦

L2：10 变体 10 个唯一场景哈希（种子记录=可复现随机）

L3：table_height 差 12mm>5mm FAIL，其余 PASS -> 提示修正仿真布局

## 5. 参数白皮书

| 参数 | 默认 | 说明 |
| 资产必填 | 5 项 | 入库门禁 |
| TOL_MM | 5-10mm | 孪生容差按任务 |
| 场景哈希 | sha1[:12] | 版本可追溯 |

## 6. Top5 踩坑

1. 资产缺碰撞体就导入：门禁先行（L1）。
2. 变体随机不可复现：记录种子+参数（L2）。
3. 尺寸"看着像"：用实测数据核对（L3）。
4. 只做视觉像不做物理像：分层孪生。
5. 场景版本没记录：变体哈希入库。

## 7. 改造指南

- 场景清单 JSON 化后由 L1 批量校验；
- 变体参数按第7章场景矩阵配置；
- L3 real/sim JSON 由现场测量与仿真导出脚本生成。

## 8. 进阶方向：变体自动生成训练数据（接第27章）、迁移评测驱动孪生精度迭代。
