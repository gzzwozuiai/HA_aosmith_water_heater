# A.O. Smith 净水加热一体机 · Home Assistant 集成

通过 A.O.史密斯（AiLink）云接口接入净水加热一体机，型号 **DR1600HF1**。
接入 Home Assistant 后，可用自带的 **HomeKit Bridge** 桥接进 Apple「家庭」App，
用 Siri 和快捷指令控制。

> 非官方集成，接口来自 App 抓包，A.O.史密斯随时可能变更或失效。

## 提供的实体

| 实体 | 说明 |
| --- | --- |
| `switch` 加热 | 下发 `SetHeaterOnOff`，桥接到 HomeKit 后即为一个开关 |
| `sensor` 热水温度 | `hotWaterTemp`，°C，可桥接为 HomeKit 温度传感器 |
| `sensor` 今日用水量 | `waterDayUse`，L |
| `sensor` N 号滤芯寿命 | `filterLifetime1..4`，%，按 `filterGrade` 上报的级数创建 |
| `sensor` TDS | `nowTDS`，仅在 `supTds` 为 1 时创建 |
| `binary_sensor` 加热中 | `heating`，加热管当前是否在工作 |
| `binary_sensor` 故障 | `errorCode != 0` |
| `binary_sensor` 童锁 | `childLockStatus` |

## 安装

1. HACS → 右上角三点 → *Custom repositories*，添加
   `https://github.com/gzzwozuiai/ha_aosmith_water_heater`，类别选 *Integration*
2. 安装后重启 Home Assistant
3. *设置 → 设备与服务 → 添加集成*，搜索 **A.O. Smith Water Heater**

## 配置

抓包 A.O.史密斯 App 对 `ailink-api.hotwater.com.cn` 的任意一个请求，取三个值：

| 字段 | 来源 |
| --- | --- |
| Access Token | 请求头 `Authorization: Bearer <token>` |
| User ID | 请求头 `Userid`，或请求体 `userId` |
| Family ID | 请求体 `familyId` |

填完后集成会自动拉取该家庭下的设备列表让你选，**不需要手填 deviceId**。

### ⚠️ 令牌 30 分钟就会过期

抓到的 JWT `exp - iat = 1800` 秒。过期后 HA 会弹出「重新认证」，
但每半小时手动重抓一次显然不可用。

要彻底解决，需要抓 App 的**登录**或**令牌刷新**请求（JWT 载荷里带了
`refreshToken` 字段，说明存在刷新接口）。拿到之后就能在集成里自动续期。
在那之前，这个集成只适合短时间测试。

### 加热开关对应哪个字段

设备一次上报 90 个属性，但没有任何一个明确标注对应 `SetHeaterOnOff`。
候选项是 `boiling` / `heating` / `powerStatus` / `warmModel` /
`heatingMachineStatus1` / `workStatus`，默认取 **`boiling`**。

确认方法：在 HA 里打开开关实体，*属性*里列出了全部候选字段的当前值；
手动开关一次，看哪个字段跟着翻转，然后在集成的*配置*里改成那个字段。

## 接入 Apple 家庭 App

Home Assistant 自带 HomeKit Bridge，不需要额外装东西。

1. *设置 → 设备与服务 → 添加集成 → **HomeKit Bridge***
2. 域选 **Switch**（想把水温也带过去就再加 **Sensor**），下一步勾选本集成的实体
3. 通知栏出现配对二维码，用 iPhone「家庭」App 扫码添加

或写在 `configuration.yaml` 里，精确控制桥接哪些实体：

```yaml
homekit:
  - name: AOSmith Bridge
    filter:
      include_entities:
        - switch.jing_shui_ji_heating
        - sensor.jing_shui_ji_hot_water_temperature
```

实体 ID 以实际生成的为准，可在*开发者工具 → 状态*里查。

### 注意事项

- HA 与 iPhone 必须在**同一个二层网络**，mDNS/Bonjour 要能通。
  Docker 部署必须用 `network_mode: host`，否则配对无法完成。
- 想在外网用 Siri，家里需要有常驻的 HomeKit 中枢（HomePod / Apple TV / 常插电的 iPad）。
- 云端轮询间隔 60 秒，且设备本身上报有延迟，HomeKit 里的状态不是实时的。
  下发指令后本集成会乐观显示新状态，最多保持 3 个轮询周期。

## 调试

```yaml
logger:
  default: warning
  logs:
    custom_components.aosmith_water_heater: debug
```

## 安全提示

抓包文件里含有 Bearer 令牌、userId、familyId 和设备 MAC。
本仓库是公开的，`Request and Response/` 已加入 `.gitignore`，不要提交上去。

## License

MIT
