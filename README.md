# Polymarket 异常交易监测 Bot

功能概要：
- 监控 Polymarket 的政治类/重大事件类市场的交易
- 检测三类异常信号：
  1. 新钱包（钱包在链上首次交易 < 24 小时）且在 Polymarket 上有首次交易
  2. 单笔下注金额 >= 5000 USDC
  3. 同一钱包在同一市场 24 小时内下单 >= 3 次
- 触发任一信号都会发送邮件告警，邮件标题包含「Polymarket异常警报」，正文包含钱包地址、交易金额、市场名称

设计原则：
- 可配置：通过环境变量指定 Polymarket API、Etherscan/Alchemy Key、SMTP 等
- 插件式：支持多种 Polymarket 数据源适配器（GraphQL/REST/mock）
- 不进行任何自动交易，纯告警

快速开始
1. 创建并激活 Python 虚拟环境
2. 安装依赖：
   pip install -r requirements.txt
3. 复制 `config.example.env` 为 `.env` 并填写你的 API Key / SMTP 配置
4. 运行：
   python run_monitor.py

注意：当前实现使用可配置的适配器来获取交易数据；如果你能提供 Polymarket 的具体 API 端点或 API key，我可以把适配器直接接上真实 API 并做最终调试。

使用 Gamma GraphQL API（示例）🛰️
- 将 `POLY_SOURCE_TYPE` 设为 `graphql`，并把 `POLY_SOURCE_URL` 设为 `https://gamma-api.polymarket.com/`。
- 如需按关键词过滤政治/重大事件类市场，可在 `.env` 中设置 `POLY_MARKET_KEYWORDS=election,president,war,conflict,china`（逗号分隔，大小写不敏感）。
- 如果你已有适合的 GraphQL 查询，也可以把查询文本放入 `POLY_GRAPHQL_TRADES_QUERY`（整段查询），系统会优先使用自定义查询。

公共子图（推荐）📡
Polymarket 有官方 subgraph，可在 The Graph 或 Goldsky 上公开查询（无需 Gamma 的浏览器认证）。已新增对公共子图的支持：
- `POLY_SUBGRAPH_URL`：设置为 Polymarket 的 subgraph URL（示例：`https://api.thegraph.com/subgraphs/name/Polymarket/polymarket-subgraph`）。
- 或将 `POLY_SOURCE_TYPE` 设为 `thegraph` 并确保 `POLY_SUBGRAPH_URL` 指向有效 URL。

如何查找子图 URL：
- Polymarket 的 subgraphs 在 The Graph / Goldsky 上公开托管；你可以在 https://thegraph.com/explorer 搜索 `Polymarket`，或直接使用 `https://api.thegraph.com/subgraphs/name/Polymarket/polymarket-subgraph`（若可用）。

演示（快速验证） ✅

- 使用公共子图进行一次抓取并查看样例交易：
  1. 在 `.env` 中设置（例如使用 Goldsky 的活动子图）：
     ```
     POLY_SOURCE_TYPE=thegraph
     POLY_SUBGRAPH_URL=https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/activity-subgraph/0.0.4/gn
     POLY_MARKET_KEYWORDS=election,president,war
     ```
  2. 运行一次抓取（不会持续运行）：
     ```bash
     PYTHONPATH=$(pwd) python3 scripts/run_once.py
     ```
  3. 若想模拟告警（无须外部 API）：
     ```bash
     PYTHONPATH=$(pwd) python3 scripts/demo_alerts.py
     ```
     该脚本会触发：单笔大额告警、同一钱包高频告警、新钱包告警（若未配置 SMTP，会显示“SMTP or recipient not configured; skipping email”）。

示例 `.env` 配置（使用公共子图）：

```
POLY_SOURCE_TYPE=thegraph
POLY_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/Polymarket/polymarket-subgraph
POLY_MARKET_KEYWORDS=election,president,war
```

