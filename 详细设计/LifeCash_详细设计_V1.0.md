# LifeCash - 详细设计文档

> 版本: 1.0 | 日期: 2026-04-27

---

## 一、核心类设计

### 1.1 GameEngine 类
```javascript
class GameEngine {
  constructor() {
    this.gameState = null;
    this.player = null;
    this.gameMap = null;
    this.eventSystem = null;
    this.uiManager = null;
    this.isRunning = false;
    this.isPaused = false;
    this.lastUpdateTime = 0;
  }

  // 初始化游戏
  init(mode, options) {
    this.gameState = new GameState(mode, options);
    this.player = new Player(options.career);
    this.gameMap = new GameMap();
    this.eventSystem = new EventSystem();
    this.uiManager = new UIManager(this);
    this.bindEvents();
  }

  // 游戏主循环
  gameLoop(timestamp) {
    if (!this.isRunning || this.isPaused) return;
    
    const deltaTime = timestamp - this.lastUpdateTime;
    this.lastUpdateTime = timestamp;
    
    this.update(deltaTime);
    this.render();
    
    requestAnimationFrame((t) => this.gameLoop(t));
  }

  // 更新游戏状态
  update(deltaTime) {
    this.player.update(deltaTime);
    this.eventSystem.checkEvents(this.player);
    this.gameState.update(deltaTime);
  }

  // 渲染
  render() {
    this.uiManager.render();
  }

  // 开始游戏
  start() {
    this.isRunning = true;
    this.lastUpdateTime = performance.now();
    requestAnimationFrame((t) => this.gameLoop(t));
  }

  // 暂停
  pause() {
    this.isPaused = true;
    this.saveGame();
  }

  // 继续
  resume() {
    this.isPaused = false;
    this.lastUpdateTime = performance.now();
  }

  // 存档
  saveGame() {
    const saveData = {
      version: '1.0',
      timestamp: Date.now(),
      player: this.player.serialize(),
      gameState: this.gameState.serialize()
    };
    localStorage.setItem('lifecash_save', JSON.stringify(saveData));
  }

  // 读档
  loadGame() {
    const saveData = JSON.parse(localStorage.getItem('lifecash_save'));
    if (saveData) {
      this.player.deserialize(saveData.player);
      this.gameState.deserialize(saveData.gameState);
    }
  }
}
```

### 1.2 Player 类
```javascript
class Player {
  constructor(careerType) {
    this.id = this.generateId();
    this.name = '';
    this.career = CareerFactory.create(careerType);
    
    // 核心属性
    this.attributes = {
      health: 100,
      happiness: 100,
      money: this.career.startMoney,
      assets: 0,
      experience: 0,
      level: 1
    };
    
    // 时间系统
    this.time = {
      daily: 24,
      used: 0,
      day: 1
    };
    
    // 技能和资产
    this.skills = [];
    this.inventory = [];
    this.investments = [];
    
    // 状态
    this.status = 'normal'; // normal, bankrupt, free, rich
  }

  // 工作
  work() {
    const result = this.career.work(this);
    this.attributes.money += result.income;
    this.attributes.health -= result.healthCost;
    this.attributes.happiness -= result.happinessCost;
    this.time.used += result.timeCost;
    this.attributes.experience += result.expGain;
    this.checkLevelUp();
    return result;
  }

  // 投资
  invest(type, amount) {
    const investment = InvestmentFactory.create(type, amount);
    if (this.attributes.money >= amount) {
      this.attributes.money -= amount;
      this.investments.push(investment);
      return { success: true, investment };
    }
    return { success: false, message: '资金不足' };
  }

  // 休息
  rest(hours) {
    this.attributes.health = Math.min(100, this.attributes.health + hours * 2);
    this.attributes.happiness = Math.min(100, this.attributes.happiness + hours);
    this.time.used += hours;
  }

  // 社交
  socialize() {
    this.attributes.happiness = Math.min(100, this.attributes.happiness + 10);
    this.time.used += 2;
  }

  // 检查升级
  checkLevelUp() {
    const expNeeded = this.attributes.level * 100;
    if (this.attributes.experience >= expNeeded) {
      this.attributes.level++;
      this.attributes.experience -= expNeeded;
      this.onLevelUp();
    }
  }

  // 升级回调
  onLevelUp() {
    this.attributes.health = Math.min(100, this.attributes.health + 5);
    this.attributes.happiness = Math.min(100, this.attributes.happiness + 5);
    this.career.onLevelUp(this);
  }

  // 结算一天
  endDay() {
    // 被动收入
    const passiveIncome = this.calculatePassiveIncome();
    this.attributes.money += passiveIncome;
    
    // 重置时间
    this.time.used = 0;
    this.time.day++;
    
    // 事件检查
    this.checkStatus();
  }

  // 计算被动收入
  calculatePassiveIncome() {
    return this.investments.reduce((sum, inv) => {
      return sum + inv.getMonthlyIncome();
    }, 0);
  }

  // 检查状态
  checkStatus() {
    // 破产检查
    if (this.attributes.money < -10000 && this.attributes.assets === 0) {
      this.status = 'bankrupt';
      return;
    }
    
    // 财务自由检查
    const monthlyExpense = this.calculateMonthlyExpense();
    const passiveIncome = this.calculatePassiveIncome();
    if (passiveIncome >= monthlyExpense && this.attributes.money > 0) {
      this.status = 'free';
      if (this.attributes.assets > 1000000) {
        this.status = 'rich';
      }
    }
  }

  // 计算月支出
  calculateMonthlyExpense() {
    const baseExpense = 3000;
    const lifestyleCost = this.attributes.level * 200;
    return baseExpense + lifestyleCost;
  }

  // 序列化
  serialize() {
    return {
      id: this.id,
      name: this.name,
      career: this.career.type,
      attributes: this.attributes,
      time: this.time,
      skills: this.skills,
      inventory: this.inventory,
      investments: this.investments.map(i => i.serialize()),
      status: this.status
    };
  }

  // 反序列化
  deserialize(data) {
    Object.assign(this, data);
    this.career = CareerFactory.create(data.career);
    this.investments = data.investments.map(i => InvestmentFactory.deserialize(i));
  }

  generateId() {
    return 'player_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
}
```

### 1.3 Career 职业类
```javascript
class Career {
  constructor(config) {
    this.type = config.type;
    this.name = config.name;
    this.startMoney = config.startMoney;
    this.baseSalary = config.baseSalary;
    this.healthCost = config.healthCost;      // 每日健康消耗
    this.happinessCost = config.happinessCost; // 每日幸福消耗
    this.timeCost = config.timeCost;          // 每日时间消耗
    this.skill = config.skill;                // 特殊技能
    this.growthRate = config.growthRate;       // 成长率
  }

  work(player) {
    const salary = this.baseSalary * (1 + player.attributes.level * 0.1);
    return {
      income: salary / 30, // 日工资
      healthCost: this.healthCost,
      happinessCost: this.happinessCost,
      timeCost: this.timeCost,
      expGain: 10
    };
  }

  onLevelUp(player) {
    // 职业特殊升级效果
    if (this.skill === '商业洞察') {
      player.investments.forEach(i => i.risk *= 0.95);
    }
  }
}

// 职业工厂
class CareerFactory {
  static careers = {
    worker: {
      type: 'worker',
      name: '工薪族',
      startMoney: 10000,
      baseSalary: 5000,
      healthCost: 2,
      happinessCost: 2,
      timeCost: 8,
      skill: null,
      growthRate: 1.0
    },
    freelancer: {
      type: 'freelancer',
      name: '自由职业者',
      startMoney: 5000,
      baseSalary: 3000,
      healthCost: 1,
      happinessCost: 1,
      timeCost: 6,
      skill: '接单加速',
      growthRate: 1.2
    },
    entrepreneur: {
      type: 'entrepreneur',
      name: '创业者',
      startMoney: 50000,
      baseSalary: 0,
      healthCost: 4,
      happinessCost: 2,
      timeCost: 12,
      skill: '商业洞察',
      growthRate: 1.5
    },
    civilServant: {
      type: 'civilServant',
      name: '公务员',
      startMoney: 8000,
      baseSalary: 4000,
      healthCost: 1,
      happinessCost: 0.5,
      timeCost: 6,
      skill: '人脉广',
      growthRate: 0.8
    },
    investor: {
      type: 'investor',
      name: '投资人',
      startMoney: 100000,
      baseSalary: 0,
      healthCost: 1,
      happinessCost: 1,
      timeCost: 3,
      skill: '财务分析',
      growthRate: 1.3
    },
    teacher: {
      type: 'teacher',
      name: '教师',
      startMoney: 6000,
      baseSalary: 4500,
      healthCost: 1,
      happinessCost: 0.5,
      timeCost: 6,
      skill: '教育加成',
      growthRate: 0.9
    }
  };

  static create(type) {
    const config = this.careers[type];
    if (!config) throw new Error('未知职业类型: ' + type);
    return new Career(config);
  }
}
```

### 1.4 Investment 投资类
```javascript
class Investment {
  constructor(config) {
    this.id = 'inv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    this.type = config.type;
    this.name = config.name;
    this.amount = config.amount;
    this.risk = config.risk;
    this.returnRate = config.returnRate;
    this.liquidity = config.liquidity;
    this.purchaseDate = Date.now();
  }

  getMonthlyIncome() {
    return this.amount * this.returnRate / 12;
  }

  getValue() {
    return this.amount;
  }

  sell(marketCondition = 1) {
    const sellValue = this.amount * this.liquidity * marketCondition;
    return sellValue;
  }

  serialize() {
    return {
      id: this.id,
      type: this.type,
      name: this.name,
      amount: this.amount,
      risk: this.risk,
      returnRate: this.returnRate,
      liquidity: this.liquidity,
      purchaseDate: this.purchaseDate
    };
  }
}

// 投资工厂
class InvestmentFactory {
  static types = {
    deposit: { name: '银行存款', risk: 0.01, returnRate: 0.03, liquidity: 1.0 },
    bond: { name: '国债', risk: 0.05, returnRate: 0.04, liquidity: 0.95 },
    fund: { name: '基金', risk: 0.3, returnRate: 0.15, liquidity: 0.8 },
    stock: { name: '股票', risk: 0.5, returnRate: 0.2, liquidity: 0.9 },
    house: { name: '房产', risk: 0.2, returnRate: 0.08, liquidity: 0.3 },
    gold: { name: '黄金', risk: 0.3, returnRate: 0.1, liquidity: 0.7 },
    startup: { name: '创业', risk: 0.8, returnRate: 0.5, liquidity: 0.1 }
  };

  static create(type, amount) {
    const config = this.types[type];
    if (!config) throw new Error('未知投资类型: ' + type);
    return new Investment({
      type,
      name: config.name,
      amount,
      risk: config.risk,
      returnRate: config.returnRate,
      liquidity: config.liquidity
    });
  }

  static deserialize(data) {
    return new Investment(data);
  }
}
```

### 1.5 EventSystem 事件系统
```javascript
class EventSystem {
  constructor() {
    this.eventQueue = [];
    this.eventHistory = [];
  }

  // 生成随机事件
  generateRandomEvent(player) {
    const events = this.getAvailableEvents(player);
    const weights = events.map(e => e.weight);
    const totalWeight = weights.reduce((a, b) => a + b, 0);
    let random = Math.random() * totalWeight;
    
    for (let i = 0; i < events.length; i++) {
      random -= weights[i];
      if (random <= 0) {
        return events[i];
      }
    }
    return events[0];
  }

  // 获取可用事件
  getAvailableEvents(player) {
    return [
      // 机会类
      { id: 'stock_tip', type: 'opportunity', name: '股市内幕', weight: 10, effect: (p) => { p.attributes.money += 5000; return '获得股市内幕消息，盈利5000元'; }},
      { id: 'house_deal', type: 'opportunity', name: '房产机会', weight: 8, effect: (p) => { return '发现一套低价房产，是否投资？'; }},
      { id: 'partner', type: 'opportunity', name: '创业合伙人', weight: 5, effect: (p) => { return '有人邀请你一起创业'; }},
      
      // 风险类
      { id: 'illness', type: 'risk', name: '突发疾病', weight: 8, effect: (p) => { p.attributes.health -= 20; p.attributes.money -= 3000; return '突发疾病，花费3000元，健康-20'; }},
      { id: 'unemployment', type: 'risk', name: '失业危机', weight: 5, effect: (p) => { return '公司裁员，可能失业'; }},
      { id: 'market_crash', type: 'risk', name: '市场波动', weight: 10, effect: (p) => { p.investments.forEach(i => i.amount *= 0.9); return '市场下跌10%'; }},
      
      // 社交类
      { id: 'wedding', type: 'social', name: '朋友婚礼', weight: 15, effect: (p) => { p.attributes.money -= 500; p.attributes.happiness += 5; return '参加婚礼，红包500元，幸福+5'; }},
      { id: 'mentor', type: 'social', name: '贵人相助', weight: 5, effect: (p) => { p.attributes.experience += 50; return '遇到贵人，获得经验+50'; }},
      { id: 'family_time', type: 'social', name: '家庭聚会', weight: 20, effect: (p) => { p.attributes.happiness += 10; return '家庭聚会，幸福+10'; }},
      
      // 随机类
      { id: 'lottery', type: 'random', name: '彩票中奖', weight: 2, effect: (p) => { p.attributes.money += 10000; return '彩票中奖10000元！'; }},
      { id: 'traffic', type: 'random', name: '交通违章', weight: 10, effect: (p) => { p.attributes.money -= 200; return '交通违章罚款200元'; }}
    ];
  }

  // 执行事件
  executeEvent(event, player) {
    const result = event.effect(player);
    this.eventHistory.push({
      event,
      playerId: player.id,
      timestamp: Date.now(),
      result
    });
    return result;
  }

  // 检查并触发事件
  checkEvents(player) {
    if (Math.random() < 0.3) { // 30%概率触发事件
      const event = this.generateRandomEvent(player);
      return this.executeEvent(event, player);
    }
    return null;
  }
}
```

### 1.6 GameMap 地图类
```javascript
class GameMap {
  constructor() {
    this.nodes = [];
    this.currentPosition = 0;
    this.init();
  }

  init() {
    // 创建地图节点
    const nodeTypes = ['work', 'opportunity', 'market', 'rest', 'social', 'health', 'random'];
    const nodeNames = {
      work: '工作格',
      opportunity: '机会格',
      market: '市场格',
      rest: '休息格',
      social: '社交格',
      health: '健康格',
      random: '随机格'
    };
    
    // 生成36个节点（6x6格子）
    for (let i = 0; i < 36; i++) {
      const type = this.getNodeType(i, nodeTypes);
      this.nodes.push({
        id: i,
        type: type,
        name: nodeNames[type],
        x: (i % 6) * 100 + 50,
        y: Math.floor(i / 6) * 100 + 50,
        visited: false
      });
    }
  }

  getNodeType(index, types) {
    // 按位置分配类型，保证游戏平衡
    const distribution = [0, 0, 1, 0, 2, 0, 3, 1, 0, 4, 0, 1, 2, 0, 5, 0, 1, 3, 0, 4, 1, 0, 6, 0, 1, 0, 2, 0, 3, 0, 0, 1, 0, 4, 0, 2];
    return types[distribution[index] || 0];
  }

  move(steps) {
    this.currentPosition = (this.currentPosition + steps) % this.nodes.length;
    this.nodes[this.currentPosition].visited = true;
    return this.nodes[this.currentPosition];
  }

  getCurrentNode() {
    return this.nodes[this.currentPosition];
  }

  render(ctx) {
    // 绘制节点和连线
    this.nodes.forEach((node, index) => {
      const color = this.getNodeColor(node.type);
      ctx.beginPath();
      ctx.arc(node.x, node.y, 30, 0, Math.PI * 2);
      ctx.fillStyle = index === this.currentPosition ? '#FFD700' : color;
      ctx.fill();
      ctx.stroke();
      
      // 绘制节点名称
      ctx.fillStyle = '#000';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(node.name, node.x, node.y + 45);
    });
  }

  getNodeColor(type) {
    const colors = {
      work: '#90EE90',
      opportunity: '#87CEEB',
      market: '#FFA07A',
      rest: '#DDA0DD',
      social: '#F0E68C',
      health: '#98FB98',
      random: '#D3D3D3'
    };
    return colors[type] || '#FFF';
  }
}
```

---

## 二、UI组件设计

### 2.1 UIManager 类
```javascript
class UIManager {
  constructor(gameEngine) {
    this.engine = gameEngine;
    this.elements = {};
    this.init();
  }

  init() {
    this.createMainLayout();
    this.bindEvents();
  }

  createMainLayout() {
    document.body.innerHTML = `
      <div id="game-container">
        <div id="header">
          <h1>LifeCash 💰</h1>
          <div id="menu-buttons">
            <button id="btn-save">存档</button>
            <button id="btn-load">读档</button>
            <button id="btn-settings">设置</button>
          </div>
        </div>
        <div id="player-status">
          <div id="player-info">
            <span id="player-career">职业: 工薪族</span>
            <span id="player-money">💰 ¥50,000</span>
            <span id="player-day">📅 第1天</span>
          </div>
          <div id="attributes">
            <span id="health">❤️ 健康: 100</span>
            <span id="happiness">😊 幸福: 100</span>
            <span id="level">⭐ 等级: 1</span>
          </div>
          <div id="time-bar">
            <span>⏰ 时间: 0/24</span>
            <progress id="time-progress" value="0" max="24"></progress>
          </div>
        </div>
        <div id="game-map">
          <canvas id="map-canvas" width="600" height="600"></canvas>
        </div>
        <div id="actions">
          <button id="btn-work" class="action-btn">🎯 工作</button>
          <button id="btn-invest" class="action-btn">💹 投资</button>
          <button id="btn-rest" class="action-btn">😴 休息</button>
          <button id="btn-social" class="action-btn">👥 社交</button>
          <button id="btn-skill" class="action-btn">📊 技能</button>
          <button id="btn-end-day" class="action-btn">🌙 结束今天</button>
        </div>
        <div id="event-modal" class="modal hidden">
          <div class="modal-content">
            <h2 id="event-title">事件</h2>
            <p id="event-description"></p>
            <button id="event-confirm">确定</button>
          </div>
        </div>
        <div id="investment-modal" class="modal hidden">
          <div class="modal-content">
            <h2>💹 投资中心</h2>
            <div id="investment-options"></div>
            <button id="investment-close">关闭</button>
          </div>
        </div>
      </div>
    `;
    
    this.elements = {
      playerCareer: document.getElementById('player-career'),
      playerMoney: document.getElementById('player-money'),
      playerDay: document.getElementById('player-day'),
      health: document.getElementById('health'),
      happiness: document.getElementById('happiness'),
      level: document.getElementById('level'),
      timeProgress: document.getElementById('time-progress'),
      mapCanvas: document.getElementById('map-canvas'),
      eventModal: document.getElementById('event-modal'),
      eventTitle: document.getElementById('event-title'),
      eventDescription: document.getElementById('event-description'),
      investmentModal: document.getElementById('investment-modal'),
      investmentOptions: document.getElementById('investment-options')
    };
  }

  bindEvents() {
    document.getElementById('btn-work').addEventListener('click', () => this.engine.player.work());
    document.getElementById('btn-invest').addEventListener('click', () => this.showInvestmentPanel());
    document.getElementById('btn-rest').addEventListener('click', () => this.engine.player.rest(4));
    document.getElementById('btn-social').addEventListener('click', () => this.engine.player.socialize());
    document.getElementById('btn-end-day').addEventListener('click', () => this.endDay());
    document.getElementById('btn-save').addEventListener('click', () => this.engine.saveGame());
    document.getElementById('btn-load').addEventListener('click', () => this.engine.loadGame());
    document.getElementById('event-confirm').addEventListener('click', () => this.hideEventModal());
    document.getElementById('investment-close').addEventListener('click', () => this.hideInvestmentModal());
  }

  render() {
    const player = this.engine.player;
    const attrs = player.attributes;
    
    this.elements.playerCareer.textContent = `职业: ${player.career.name}`;
    this.elements.playerMoney.textContent = `💰 ¥${attrs.money.toLocaleString()}`;
    this.elements.playerDay.textContent = `📅 第${player.time.day}天`;
    this.elements.health.textContent = `❤️ 健康: ${attrs.health}`;
    this.elements.happiness.textContent = `😊 幸福: ${attrs.happiness}`;
    this.elements.level.textContent = `⭐ 等级: ${attrs.level}`;
    this.elements.timeProgress.value = player.time.used;
    
    // 渲染地图
    const ctx = this.elements.mapCanvas.getContext('2d');
    ctx.clearRect(0, 0, 600, 600);
    this.engine.gameMap.render(ctx);
  }

  showEventModal(title, description) {
    this.elements.eventTitle.textContent = title;
    this.elements.eventDescription.textContent = description;
    this.elements.eventModal.classList.remove('hidden');
  }

  hideEventModal() {
    this.elements.eventModal.classList.add('hidden');
  }

  showInvestmentPanel() {
    const options = Object.entries(InvestmentFactory.types).map(([type, config]) => `
      <div class="investment-option">
        <h3>${config.name}</h3>
        <p>风险: ${config.risk * 100}% | 年化: ${config.returnRate * 100}%</p>
        <input type="number" id="invest-${type}" placeholder="金额" min="100" step="100">
        <button data-type="${type}">投资</button>
      </div>
    `).join('');
    
    this.elements.investmentOptions.innerHTML = options;
    this.elements.investmentModal.classList.remove('hidden');
    
    // 绑定投资按钮
    this.elements.investmentOptions.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const type = e.target.dataset.type;
        const input = document.getElementById(`invest-${type}`);
        const amount = parseInt(input.value) || 0;
        if (amount > 0) {
          this.engine.player.invest(type, amount);
          this.render();
        }
      });
    });
  }

  hideInvestmentModal() {
    this.elements.investmentModal.classList.add('hidden');
  }

  endDay() {
    this.engine.player.endDay();
    const event = this.engine.eventSystem.checkEvents(this.engine.player);
    if (event) {
      this.showEventModal('随机事件', event);
    }
    this.render();
  }
}
```

---

## 三、样式设计

### 3.1 CSS 样式
```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

#game-container {
  width: 800px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

#header {
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

#header h1 {
  font-size: 28px;
}

#menu-buttons button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 10px 20px;
  margin-left: 10px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

#menu-buttons button:hover {
  background: rgba(255, 255, 255, 0.4);
}

#player-status {
  background: #f8f9fa;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
}

#player-info, #attributes {
  display: flex;
  gap: 30px;
  margin-bottom: 10px;
}

#player-info span, #attributes span {
  font-size: 16px;
  font-weight: 500;
}

#time-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

#time-progress {
  flex: 1;
  height: 10px;
  border-radius: 5px;
  appearance: none;
  background: #e0e0e0;
}

#time-progress::-webkit-progress-bar {
  background: #e0e0e0;
  border-radius: 5px;
}

#time-progress::-webkit-progress-value {
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  border-radius: 5px;
}

#game-map {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: #f0f0f0;
}

#map-canvas {
  background: white;
  border-radius: 10px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
}

#actions {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.action-btn {
  padding: 15px;
  font-size: 18px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
}

#btn-work { background: #90EE90; }
#btn-invest { background: #87CEEB; }
#btn-rest { background: #DDA0DD; }
#btn-social { background: #F0E68C; }
#btn-skill { background: #FFA07A; }
#btn-end-day { background: #FFD700; grid-column: span 3; }

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal.hidden {
  display: none;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 15px;
  max-width: 500px;
  text-align: center;
}

.modal-content h2 {
  margin-bottom: 20px;
  color: #4facfe;
}

.modal-content button {
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 20px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 20px;
}

.investment-option {
  border: 1px solid #e0e0e0;
  padding: 15px;
  margin: 10px 0;
  border-radius: 10px;
}

.investment-option input {
  width: 100px;
  padding: 8px;
  margin: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.investment-option button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 5px;
  cursor: pointer;
}
```

---

## 四、多人接口设计

### 4.1 客户端 WebSocket
```javascript
class MultiplayerClient {
  constructor(serverUrl) {
    this.socket = null;
    this.roomId = null;
    this.playerId = null;
    this.callbacks = {};
  }

  connect(serverUrl) {
    this.socket = new WebSocket(serverUrl);
    
    this.socket.onopen = () => {
      console.log('WebSocket连接成功');
    };
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.socket.onclose = () => {
      console.log('WebSocket连接关闭');
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'room_state':
        this.callbacks.onRoomState?.(data.payload);
        break;
      case 'game_state':
        this.callbacks.onGameState?.(data.payload);
        break;
      case 'chat_message':
        this.callbacks.onChatMessage?.(data.payload);
        break;
      case 'error':
        console.error('服务器错误:', data.message);
        break;
    }
  }

  joinRoom(roomId, playerData) {
    this.send('join_room', { roomId, player: playerData });
  }

  leaveRoom() {
    this.send('leave_room', { roomId: this.roomId });
  }

  sendAction(action, payload) {
    this.send('player_action', { roomId: this.roomId, action, payload });
  }

  send(type, payload) {
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, payload }));
    }
  }

  on(event, callback) {
    this.callbacks[event] = callback;
  }
}
```

---

**文档状态**: 完成
**下一步**: 编写完整游戏代码