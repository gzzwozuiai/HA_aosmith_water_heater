# 热水器开关集成

## 功能特性
- 通过Home Assistant控制热水器开关
- 实时状态反馈
- 安全认证配置

## 安装步骤
1. 通过HACS添加本仓库
2. 重启Home Assistant
3. 前往 `配置 > 设备与服务 > 添加集成`
4. 搜索并选择 `HotWater Switch`
5. 输入以下参数：
   - **Access Token**: 从APP获取的Bearer Token
   - **User ID**: 用户唯一标识
   - **Family ID**: 家庭组标识

## 故障排除
- 查看日志命令：
  ```bash
  grep -i 'hotwater_switch' /config/home-assistant.log
