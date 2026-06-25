---
title: "2025 前端面试题大全"
date: 2026-06-25
draft: false
categories: ["前端"]
tags: ["前端", "面试", "JavaScript", "Vue", "React", "2025"]
---

## 前言

2025 年前端技术持续演进，面试题目也在不断更新。本文整理了最新的前端面试高频题目，涵盖 JavaScript 基础、框架原理、性能优化、工程化等核心领域，帮助大家系统备战面试。

## 一、JavaScript 基础

### 1.1 闭包的理解

闭包是指函数能够访问其词法作用域中变量的能力，即使该函数在其词法作用域之外执行。

```javascript
function createCounter() {
  let count = 0;
  return function () {
    return ++count;
  };
}
const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2
```

闭包的常见应用场景：

- 数据封装和私有变量
- 函数工厂
- 回调函数和事件处理
- 柯里化（Currying）

### 1.2 原型链与继承

每个对象都有一个 `__proto__` 指向其构造函数的 `prototype`，形成原型链。当访问对象属性时，会沿着原型链向上查找。

```javascript
function Animal(name) {
  this.name = name;
}
Animal.prototype.speak = function () {
  return `${this.name} makes a noise.`;
};

function Dog(name) {
  Animal.call(this, name);
}
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;
```

### 1.3 Promise 与 async/await

Promise 是异步编程的解决方案，async/await 是其语法糖。

```javascript
async function fetchData() {
  try {
    const response = await fetch("/api/data");
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("请求失败:", error);
  }
}
```

手写 Promise.all 的核心思路：

```javascript
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    const results = [];
    let count = 0;
    promises.forEach((p, i) => {
      Promise.resolve(p).then((val) => {
        results[i] = val;
        if (++count === promises.length) resolve(results);
      }, reject);
    });
  });
}
```

## 二、CSS 核心知识

### 2.1 BFC（块级格式化上下文）

BFC 是一个独立的渲染区域，内部元素的布局不会影响外部。触发条件：

- `overflow` 不为 `visible`
- `display` 为 `flex`、`grid`、`inline-block` 等
- `position` 为 `absolute` 或 `fixed`
- `float` 不为 `none`

### 2.2 Flex 布局

```css
.container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
```

### 2.3 CSS 变量与主题切换

```css
:root {
  --primary-color: #1890ff;
  --bg-color: #ffffff;
}

[data-theme="dark"] {
  --primary-color: #177ddc;
  --bg-color: #141414;
}
```

## 三、Vue 面试题

### 3.1 Vue 3 响应式原理

Vue 3 使用 `Proxy` 替代了 Vue 2 的 `Object.defineProperty`，解决了：

- 无法检测对象属性的添加和删除
- 无法检测数组索引和长度的变化
- 性能更好，不需要递归遍历所有属性

```javascript
const reactive = (target) => {
  return new Proxy(target, {
    get(target, key, receiver) {
      track(target, key); // 依赖收集
      return Reflect.get(target, key, receiver);
    },
    set(target, key, value, receiver) {
      const result = Reflect.set(target, key, value, receiver);
      trigger(target, key); // 触发更新
      return result;
    },
  });
};
```

### 3.2 Vue 3 Composition API 优势

- 更好的逻辑复用（Composables）
- 更灵活的代码组织
- 更好的类型推导
- 更小的打包体积（tree-shaking）

### 3.3 虚拟 DOM 与 Diff 算法

Vue 的 Diff 算法核心策略：

- 同层比较，不跨层级
- 同节点类型才进行比较
- 使用 `key` 优化列表对比

Vue 3 引入了最长递增子序列算法优化节点移动。

## 四、React 面试题

### 4.1 React Fiber 架构

Fiber 是 React 16 引入的协调引擎，核心特点：

- **可中断渲染**：将渲染工作拆分为小单元
- **优先级调度**：高优先级更新可以打断低优先级
- **双缓存树**：current 树和 workInProgress 树

### 4.2 Hooks 原理

```javascript
// 简化版 useState 实现
let hookStates = [];
let hookIndex = 0;

function useState(initialState) {
  hookStates[hookIndex] = hookStates[hookIndex] || initialState;
  const currentIndex = hookIndex;
  function setState(newState) {
    hookStates[currentIndex] = newState;
    render(); // 触发重新渲染
  }
  return [hookStates[hookIndex++], setState];
}
```

### 4.3 React 性能优化

- `React.memo` / `useMemo` / `useCallback` 避免不必要的渲染
- 虚拟列表优化长列表
- 代码分割与懒加载
- 状态下沉，减少不必要的全局状态

## 五、工程化与构建工具

### 5.1 Vite vs Webpack

| 特性 | Vite | Webpack |
|------|------|---------|
| 开发启动 | 极快（ESM 原生加载） | 较慢（打包后启动） |
| 热更新 | 毫秒级 | 秒级 |
| 生产构建 | Rollup | 自身打包 |
| 配置复杂度 | 低 | 高 |

### 5.2 模块化方案

- **ESM**：标准模块方案，静态分析
- **CJS**：Node.js 模块方案，运行时加载
- **UMD**：兼容多种模块系统
- **AMD**：异步模块定义

### 5.3 Monorepo 方案

2025 年主流 Monorepo 工具：

- **pnpm workspace**：高效磁盘利用
- **Turborepo**：构建缓存与并行执行
- **Nx**：增量构建与依赖图分析

## 六、性能优化

### 6.1 首屏性能优化

- SSR / SSG 服务端渲染
- 关键资源预加载（`<link rel="preload">`）
- 图片懒加载与现代格式（WebP、AVIF）
- 代码分割与动态导入
- CDN 加速

### 6.2 运行时性能优化

- 防抖与节流
- Web Worker 处理耗时计算
- requestAnimationFrame 优化动画
- 虚拟滚动优化长列表

### 6.3 Core Web Vitals

- **LCP（Largest Contentful Paint）**：< 2.5s
- **INP（Interaction to Next Paint）**：< 200ms
- **CLS（Cumulative Layout Shift）**：< 0.1

## 七、TypeScript

### 7.1 高级类型工具

```typescript
// 条件类型
type IsString<T> = T extends string ? true : false;

// 映射类型
type Readonly<T> = {
  readonly [P in keyof T]: T[P];
};

// 模板字面量类型
type EventName = `on${Capitalize<string>}`;
```

### 7.2 TypeScript 体操

```typescript
// 实现 DeepPartial
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// 实现 ReturnType
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
```

## 八、网络与安全

### 8.1 HTTP/3 与 QUIC

HTTP/3 基于 QUIC 协议，优势：

- 0-RTT 连接建立
- 多路复用无队头阻塞
- 连接迁移（网络切换不断连）
- 内置 TLS 1.3

### 8.2 前端安全

- **XSS 防护**：内容安全策略（CSP）、输入过滤、输出编码
- **CSRF 防护**：SameSite Cookie、Token 验证
- **点击劫持**：X-Frame-Options、CSP frame-ancestors

## 总结

2025 年前端面试依然重视基础知识，同时对 TypeScript、性能优化、工程化能力的要求更高。建议系统学习原理，结合实际项目经验，才能在面试中脱颖而出。
