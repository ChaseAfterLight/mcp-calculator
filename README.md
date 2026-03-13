# 物种图鉴 MCP 项目

一个基于 MCP 协议的物种识别和图鉴管理系统。

## 功能特性

- 🔍 **物种识别** - AI 识别动植物并生成图鉴卡片
- 📚 **图鉴管理** - 智能存储和查询已识别物种
- 🏆 **积分系统** - 发现新物种获得积分奖励
- 📧 **邮件分享** - 将图鉴卡片发送到邮箱

## 项目结构

```
├── mcp_servers/           # MCP 服务器
│   ├── species_card_generator.py      # 图鉴卡片生成
│   ├── species_encyclopedia_mcp.py    # 图鉴管理和积分
│   └── species_card_email_service.py  # 邮件服务
├── utils/                 # 工具模块
│   ├── card_renderer.py   # 卡片渲染器
│   └── email_sender.py    # 邮件发送器
├── cards/                 # 图鉴数据
│   ├── index.json         # 物种索引
│   ├── user_scores.json   # 用户积分
│   ├── images/            # 卡片图片
│   └── metadata/          # 物种详细信息
├── templates/             # 卡片模板
└── docs/                  # 文档
```

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
playwright install chromium
```

2. 启动所有 MCP 服务：
```bash
python mcp_pipe.py
```

3. 启动前端可调用的 HTTP API 网关：
```bash
python api_gateway.py
```

默认地址：`http://127.0.0.1:8000`

## HTTP API 网关（前端直连）

- `GET /health` - 健康检查
- `POST /api/species/register` - 注册物种
- `POST /api/species/generate` 或 `POST /api/species/generate-card` - 生成图鉴卡片
- `GET /api/species/search?keyword=...&limit=50` - 搜索图鉴
- `GET /api/users/{user_id}/stats` - 查询用户积分统计
- `POST /api/species/email` - 发送图鉴卡片邮件

网关返回统一结构：

```json
{
  "success": true,
  "trace_id": "f6b4c98c2d9c4ceabde5a5d8b131d2e0",
  "data": {}
}
```

错误时返回：

```json
{
  "success": false,
  "trace_id": "f6b4c98c2d9c4ceabde5a5d8b131d2e0",
  "error": {
    "code": "MCP_REGISTER_ERROR",
    "message": "错误信息",
    "details": {}
  }
}
```

## MCP 服务

### 1. 物种图鉴管理 (species-encyclopedia)
- `register_species()` - 智能注册物种（自动检查重复+积分）
- `search_species()` - 搜索图鉴
- `get_my_stats()` - 查询积分统计

### 2. 图鉴卡片生成 (species-card-generator)  
- `generate_species_card()` - 生成宝可梦风格图鉴卡片

### 3. 邮件服务 (species-card-email-service)
- `send_species_card_email()` - 发送图鉴卡片到邮箱

## 积分规则

- 1-2星物种：+10 分
- 3星物种：+20 分  
- 4星物种：+30 分
- 5星物种：+50 分
- 重复识别：+0 分

## 使用流程

```
用户上传照片 → AI识别物种 → register_species()
    ↓
自动判断：
  - 新物种 → 添加图鉴 + 奖励积分 + generate_species_card()
  - 已存在 → 返回已有信息
    ↓
可选：send_species_card_email() 分享到邮箱
```
