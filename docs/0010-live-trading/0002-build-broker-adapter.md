# 0002 Build Broker Adapter

来源：`docs/0010-live-trading/design.md`、`docs/0010-live-trading/progress.md`

## 目标

建立券商适配器接口，并用 mock broker 完成第一版集成测试，避免早期直接连接真实券商。

## 前置依赖

- 实盘模型和安全原则已完成。
- 具体券商接口待确认。

## 执行步骤

1. 定义 `BrokerAdapter` 接口。
2. 实现 `get_account()`。
3. 实现 `get_positions()`。
4. 实现 `preview_order()`。
5. 实现 `place_order()`。
6. 实现 `cancel_order()`。
7. 实现 `get_executions()`。
8. 实现 mock broker adapter。
9. 将真实券商凭证读取逻辑隔离在后端配置层。

## 产出

- 券商适配器接口。
- mock broker adapter。
- 凭证隔离方案草案。

## 验收

- 模块可以在 mock broker 下完整测试。
- 替换真实券商时不影响业务流程层。
- 凭证不会暴露给前端。

