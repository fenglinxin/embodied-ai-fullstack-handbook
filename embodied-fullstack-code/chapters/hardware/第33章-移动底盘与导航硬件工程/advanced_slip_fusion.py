# -*- coding: utf-8 -*-
"""第33章 L3 高阶优化版：轮速-IMU 融合与打滑检测。"""
from __future__ import annotations
import math, sys

DT = 0.02
SLIP_TH = 0.3


def simulate():
    # 真实速度：0.5 匀速，2s-3s 打滑（真实前进0.1，轮子空转0.5）
    x_real = 0.0
    x_wheel = 0.0
    x_fused = 0.0
    slip_events = 0
    for i in range(250):
        t = i * DT
        slipping = 2.0 <= t < 3.0
        real_v = 0.1 if slipping else 0.5                  # 打滑时真实前进慢
        imu_v = real_v * 0.9                               # IMU近似真实(带误差)
        wheel_v = 1.2 if slipping else 0.5                 # 轮子空转/正常
        x_real += real_v * DT
        x_wheel += wheel_v * DT
        slip = abs(wheel_v - imu_v) > SLIP_TH
        if slip:
            slip_events += 1
            # 打滑时用 IMU 速度积分（近似）
            x_fused += imu_v * DT
        else:
            x_fused += wheel_v * DT
    return x_real, x_wheel, x_fused, slip_events


def main() -> int:
    real, wheel, fused, events = simulate()
    print(f"真实位移 {real:.2f} m")
    print(f"纯轮速里程 {wheel:.2f} m (误差 {(wheel-real)*100:.0f} cm)")
    print(f"融合里程 {fused:.2f} m (误差 {(fused-real)*100:.1f} cm) "
          f"检测打滑 {events} 次")
    print("打滑时：轮速与IMU矛盾->融合器用IMU积分并降速")
    return 0


if __name__ == "__main__":
    sys.exit(main())
