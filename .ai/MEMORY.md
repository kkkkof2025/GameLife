# 核心记忆

## 2026-05-23 - GitHub Pages 联机阶段完善

### 运行报错修复补记
1. GitHub Pages 上 `crash.html` 曾出现 `Uncaught SyntaxError: Unexpected token '{'`，根因定位为部分浏览器/运行环境对 class field 形式的 `LeaderboardManager = class {}` 兼容性不足。
2. 已将 `LeaderboardManager` 从 `MultiplayerManager` 内部 class field 改为普通顶层 `class LeaderboardManager`，`MultiplayerManager` 构造函数直接 `new LeaderboardManager()`。
3. 继续排查到 `catch {}` 这类可选捕获绑定也可能影响旧浏览器解析，已统一改成 `catch (err)`。
4. 后续修改 `crash.html` 时避免在 class 内使用 public class field 语法，也尽量避免 optional catch binding；GitHub Pages 是纯静态托管，没有构建转译步骤，源码语法必须能被目标浏览器直接解析。

### 2026-05-23 - 联机确认竞态修复
1. 修复客端把未包含自己玩家条目的 `room_state` 误当作加入成功的竞态。
2. 增加 `joinConfirmed` 状态，用于区分“已连上房主”与“房主已确认该玩家在房间里”，并要求确认快照里包含当前玩家自己。
3. 冒烟测试补充了客端加入确认和自我条目检查，避免只连上连接但实际房间状态未同步的假通过。

### 2026-05-24 - 多人结束状态修复
1. 修复房主最后结束时房间状态不会进入 `finished` 的问题，统一通过 `_markRoomFinishedIfComplete()` 判断所有玩家是否完成。
2. 游戏结束流程增加 `gameEnded` 幂等保护，避免计时器或重复操作导致排行榜重复写入、最终成绩重复发送。
3. `smoke-test.html` 已补充最终成绩提交和房间完成状态校验，覆盖创建、加入、开始、排行、结束的基础闭环。

### 2026-05-25 - 断线重连确认修复
1. 收紧重连确认条件：房主必须把当前玩家从 `disconnected` 恢复为活动状态，客端才算重连成功。
2. 客端断线后会先清空 `joinConfirmed`，避免把旧房间快照误判成已重连。
3. `smoke-test.html` 现在覆盖断线、自动重连、恢复同步和最终成绩的完整闭环。

### 2026-05-25 - 多人赛后结果页
1. 结束弹窗新增房间结果区，展示房间状态和最终排名，便于多人联机收尾。
2. 冒烟测试补充赛后结果页校验，确保房主和客端都能看到相同的最终房间成员信息。

### 本阶段完成
1. 保持纯静态前端，不引入项目后端，适配 GitHub Pages 部署环境。
2. 多人区域新增联机诊断面板：
   - 页面环境（HTTPS、localhost、file:// 等）
   - 当前信令服务
   - Peer ID
   - 房间状态
   - 玩家数/连接数
   - 最近事件和最近错误
3. 新增邀请链接和 Peer ID 一键复制，方便两台浏览器手动测试。
4. 新增高级联机配置：
   - 默认继续使用 PeerJS Cloud。
   - 可填写自建 PeerServer 的 host/port/path/secure。
   - 配置保存在 localStorage，创建/加入房间前自动生效。
5. 新增自定义 ICE/TURN 服务器配置：
   - 支持按行粘贴 `turn:host:port,username,credential`。
   - 诊断面板会显示当前自定义 ICE 数量，方便确认配置是否生效。
6. 创建/加入房间期间会临时禁用按钮，减少重复点击造成的连接状态错乱。
7. 新增断线重连和房主退出处理：
   - 客端与房主断开后会自动按原房主 Peer ID 重连，最多尝试 6 次。
   - 房主不再立刻删除断线玩家，而是标记为 `disconnected`，重连后恢复条目。
   - 客端会带上最近同步快照重连，房主可恢复分数、财富、等级和天数。
   - 房主主动返回菜单会广播 `room_closed`，客端收到后返回开始界面。
   - 客端主动返回菜单会发送 `leave_room`，房主移除该玩家。
   - 浏览器关闭/刷新前会尽量发送离房/关房通知，但突发断网仍依赖自动重连和连接关闭检测。
8. 新增 GitHub Pages 内置联机冒烟测试：
   - `crash.html?mock-p2p=1` 会用内置 MockPeer 替代 PeerJS，不访问公共信令。
   - `smoke-test.html` 会在同源页面中加载房主/客端两个 iframe，自动测试创建房间、邀请加入、房主开始、客端自动进入和排行同步。
   - `crash.html` 暴露 `window.ui`、`window.gameState`、`window.CONFIG`，方便后续接 Playwright 或其他浏览器自动化。
   - `smoke=1` 会跳过本地存档恢复弹窗，避免测试被 confirm 阻塞。

### GitHub Pages 测试建议
1. 房主和客端都访问同一个 GitHub Pages 地址，不要互相分享 `file://` 本地路径。
2. 房主创建房间后复制邀请链接；客端打开链接，确认诊断面板中页面环境为 HTTPS。
3. 如果公共 PeerJS 信令失败，在高级联机配置中填写同一套自建 PeerServer 配置后再创建/加入。
4. 如果能进房但数据不同步，优先看诊断面板的连接数和最近错误；如果穿透失败，继续补 TURN 配置或替换成自建 TURN。
5. 测试断线：关闭客端网络/刷新客端页面会触发自动重连；关闭房主页面则客端应显示房主关闭/断开，不会继续假在线。
6. 测试基础联机流程：打开 `smoke-test.html`，点击“运行测试”，通过后再测真实 PeerJS 网络。

## 2026-05-22 - 进度校准与多人联机修复

### 当前项目状态
LifeCash 是一个单文件为主的财富流/人生财富沙盘 Web 小游戏，当前实现是纯前端方案：

- `index.html`: 入口页，保留 query/hash 后跳转到 `crash.html`
- `crash.html`: 主游戏文件，包含 HTML/CSS/JavaScript
- `.ai/`: AI 协作记忆和项目进度
- `需求收集/`、`概要设计/`、`详细设计/`: 项目文档

### 已完成能力
1. 单人畅玩模式、限时模式、职业系统、投资系统、随机事件、存档/读档、结束报告。
2. 多人模式已从旧的本地/临时方案调整为 PeerJS + WebRTC P2P：
   - 房主创建房间，Peer ID 作为房间码。
   - 客户端通过邀请链接或 Peer ID 加入。
   - 房主负责维护房间状态和实时排行。
3. 排行榜系统：
   - 本地综合排行榜。
   - 人生赢家提名榜。
   - 可选 GitHub Gist 导入/导出/同步。

### 本次修复
1. 修复房主点击开始只启动本机的问题：房主开始后会广播 `start_room`，客端收到后自动进入游戏。
2. 修复非房主在等待阶段能误点本地开始的问题：客端等待房主开始，房间进入 `playing` 后才能进入。
3. 修复加入房间确认监听的竞态：先注册确认监听，再发送 `join_request`。
4. 清理 `crash.html` 中混入的不可见 BOM 字符。
5. 更新 README 和 AI 记忆，避免后续 AI 继续按旧的“项目代码/”目录或已删除的服务端方案推进。

### 联机判断
当前“无需后端”指项目不需要自建业务后端，但 PeerJS P2P 仍依赖：

- PeerJS 公共信令服务 `0.peerjs.com`
- WebRTC STUN/TURN 网络穿透
- 两端浏览器能访问同一个页面地址或手动输入 Peer ID

如果两台设备使用 `file://` 邀请链接，另一台设备通常打不开相同路径。可行测试方案是部署到 GitHub Pages，或在同一台机器/局域网启动静态 HTTP 服务，让两台设备访问同一个 URL。正式稳定方案是自建 PeerServer + TURN。

### 下一步优先级
1. 把 `smoke-test.html` 的页面级流程固化为可重复运行的 CI/本地 Playwright 脚本。
2. 增加观战系统。
3. 增加更细的房间历史和回放记录。
4. 优化排行榜 UI 和移动端可读性。

---
*最后更新: 2026-05-25*
