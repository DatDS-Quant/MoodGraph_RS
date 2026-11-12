/**
 * MOODGRAPH E2E TEST SUITE - HELPER MODULE
 * File: tests/test_helpers.js
 * 
 * Cung cấp môi trường giả lập DOM (Lightweight DOM Shim) và các hàm tiện ích
 * phục vụ chạy kiểm thử độc lập (Opaque-box) trong Node.js.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT_DIR = path.resolve(__dirname, '..');
const DEMO_DIR = path.join(ROOT_DIR, 'demo');

/**
 * Đọc nội dung file index.html
 */
function getIndexHtmlContent() {
  const htmlPath = path.join(DEMO_DIR, 'index.html');
  return fs.readFileSync(htmlPath, 'utf8');
}

/**
 * Đọc nội dung file js/mock_data.js
 */
function getMockDataCode() {
  const filePath = path.join(DEMO_DIR, 'js', 'mock_data.js');
  return fs.readFileSync(filePath, 'utf8');
}

/**
 * Đọc nội dung file js/academic_lab.js
 */
function getAcademicLabCode() {
  const filePath = path.join(DEMO_DIR, 'js', 'academic_lab.js');
  return fs.readFileSync(filePath, 'utf8');
}

/**
 * Đọc nội dung file js/app.js
 */
function getAppCode() {
  const filePath = path.join(DEMO_DIR, 'js', 'app.js');
  return fs.readFileSync(filePath, 'utf8');
}

/**
 * Tạo một Mock Element đơn giản
 */
class MockElement {
  constructor(tagName = 'div', id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.className = '';
    this.classList = {
      _classes: new Set(),
      add: (...classes) => {
        classes.forEach(c => this.classList._classes.add(c));
        this.className = Array.from(this.classList._classes).join(' ');
      },
      remove: (...classes) => {
        classes.forEach(c => this.classList._classes.delete(c));
        this.className = Array.from(this.classList._classes).join(' ');
      },
      contains: (c) => this.classList._classes.has(c),
      toggle: (c) => {
        if (this.classList._classes.has(c)) {
          this.classList.remove(c);
          return false;
        } else {
          this.classList.add(c);
          return true;
        }
      }
    };
    this.style = {};
    this.attributes = {};
    this.children = [];
    this.innerHTML = '';
    this.textContent = '';
    this.value = '';
    this.eventListeners = {};
  }

  getContext(type) {
    return {
      canvas: this,
      fillRect: () => {},
      clearRect: () => {},
      beginPath: () => {},
      closePath: () => {},
      moveTo: () => {},
      lineTo: () => {},
      arc: () => {},
      stroke: () => {},
      fill: () => {},
      save: () => {},
      restore: () => {},
      translate: () => {},
      scale: () => {},
      rotate: () => {},
      fillText: () => {},
      strokeText: () => {},
      measureText: () => ({ width: 50 }),
      createLinearGradient: () => ({ addColorStop: () => {} }),
      createRadialGradient: () => ({ addColorStop: () => {} }),
      setLineDash: () => {}
    };
  }

  setAttribute(key, val) {
    this.attributes[key] = String(val);
  }

  getAttribute(key) {
    return this.attributes[key] || null;
  }

  addEventListener(event, handler) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(handler);
  }

  dispatchEvent(event) {
    const type = typeof event === 'string' ? event : event.type;
    const handlers = this.eventListeners[type] || [];
    handlers.forEach(h => h(event));
  }

  getBoundingClientRect() {
    return { width: 800, height: 520, left: 0, top: 0, right: 800, bottom: 520 };
  }

  querySelector(selector) {
    if (selector.startsWith('#')) {
      const targetId = selector.substring(1);
      return this._findChild(el => el.id === targetId);
    }
    if (selector.startsWith('.')) {
      const cls = selector.substring(1);
      return this._findChild(el => el.classList.contains(cls));
    }
    return this._findChild(el => el.tagName.toLowerCase() === selector.toLowerCase());
  }

  querySelectorAll(selector) {
    const results = [];
    this._findAllChildren(selector, results);
    return results;
  }

  _findChild(predicate) {
    for (const child of this.children) {
      if (predicate(child)) return child;
      const found = child._findChild(predicate);
      if (found) return found;
    }
    return null;
  }

  _findAllChildren(selector, out) {
    for (const child of this.children) {
      let match = false;
      if (selector.startsWith('#') && child.id === selector.substring(1)) match = true;
      else if (selector.startsWith('.') && child.classList.contains(selector.substring(1))) match = true;
      else if (child.tagName.toLowerCase() === selector.toLowerCase()) match = true;

      if (match) out.push(child);
      child._findAllChildren(selector, out);
    }
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      this.children.splice(idx, 1);
    }
    return child;
  }
}

/**
 * Khởi tạo môi trường giả lập Sandbox chứa DOM và Window
 */
function createMockEnvironment() {
  const elementsById = new Map();

  function getOrCreateElement(id, tag = 'div') {
    if (!elementsById.has(id)) {
      const el = new MockElement(tag, id);
      elementsById.set(id, el);
    }
    return elementsById.get(id);
  }

  // Tạo sẵn các element quan trọng
  const rootIds = [
    'three-canvas', 'threejs-container', 'three-hud-card',
    'head-to-head-columns', 'live-session-status-banner',
    'header-persona-selector', 'header-user-avatar',
    'nav-btn-mode-a', 'nav-btn-mode-b', 'tab-mode-a', 'tab-mode-b',
    'mode-a-container', 'mode-b-container',
    'btn-persona-user1', 'btn-persona-user2', 'btn-persona-user-cold'
  ];
  rootIds.forEach(id => getOrCreateElement(id));

  const mockLocalStorage = {
    _data: {},
    getItem(k) { return this._data[k] !== undefined ? this._data[k] : null; },
    setItem(k, v) { this._data[k] = String(v); },
    removeItem(k) { delete this._data[k]; },
    clear() { this._data = {}; }
  };

  const mockDocument = {
    getElementById(id) {
      return getOrCreateElement(id);
    },
    createElement(tag) {
      return new MockElement(tag);
    },
    querySelector(sel) {
      if (sel.startsWith('#')) return getOrCreateElement(sel.substring(1));
      return new MockElement(sel);
    },
    querySelectorAll(sel) {
      return [];
    },
    addEventListener() {},
    removeEventListener() {},
    body: new MockElement('body', 'body')
  };

  let rafIdCounter = 0;
  const pendingRafs = new Map();

  function mockRaf(fn) {
    rafIdCounter++;
    pendingRafs.set(rafIdCounter, fn);
    return rafIdCounter;
  }

  function mockCancelRaf(id) {
    pendingRafs.delete(id);
  }

  function stepAnimationFrames(count = 1) {
    for (let c = 0; c < count; c++) {
      const callbacks = Array.from(pendingRafs.values());
      pendingRafs.clear();
      callbacks.forEach(fn => {
        try { fn(Date.now()); } catch (e) {}
      });
    }
  }

  const mockWindow = {
    document: mockDocument,
    localStorage: mockLocalStorage,
    sessionStorage: mockLocalStorage,
    innerWidth: 1920,
    innerHeight: 1080,
    devicePixelRatio: 1,
    addEventListener() {},
    removeEventListener() {},
    requestAnimationFrame: mockRaf,
    cancelAnimationFrame: mockCancelRaf,
    stepAnimationFrames,
    performance: { now: () => Date.now() },
    setTimeout: (fn, ms) => { /* mock no-op or fast */ return 1; },
    clearTimeout: () => {},
    setInterval: () => 1,
    clearInterval: () => {},
    WebGLRenderingContext: true
  };

  const sandbox = {
    window: mockWindow,
    document: mockDocument,
    localStorage: mockLocalStorage,
    sessionStorage: mockLocalStorage,
    console: {
      log: () => {},
      warn: () => {},
      error: () => {},
      info: () => {}
    },
    Math: Math,
    Date: Date,
    setTimeout: (fn, ms) => 1,
    clearTimeout: () => {},
    setInterval: () => 1,
    clearInterval: () => {},
    requestAnimationFrame: mockRaf,
    cancelAnimationFrame: mockCancelRaf,
    performance: { now: () => Date.now() },
    THREE: undefined
  };

  vm.createContext(sandbox);

  // 1. Chạy mock_data.js
  const mockCode = getMockDataCode();
  vm.runInContext(mockCode, sandbox);

  // 2. Chạy academic_lab.js
  const labCode = getAcademicLabCode();
  vm.runInContext(labCode, sandbox);

  // 3. Chạy app.js
  const appCode = getAppCode();
  vm.runInContext(appCode, sandbox);

  return {
    sandbox,
    window: sandbox.window,
    document: mockDocument,
    localStorage: mockLocalStorage,
    elementsById,
    stepAnimationFrames
  };
}

module.exports = {
  ROOT_DIR,
  DEMO_DIR,
  getIndexHtmlContent,
  getMockDataCode,
  getAcademicLabCode,
  getAppCode,
  createMockEnvironment
};
