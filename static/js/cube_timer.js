// 获取 DOM 元素
  const timeDisplay = document.querySelector(".time-display");
  const scrambleDisplay = document.querySelector(".scramble-display");

  // 秒表状态变量
  let timer = null;  // 计时器 ID
  let elapsedTime = 0;  // 已经过的时间（毫秒）
  let startTime = 0;  // 计时开始的时间戳
  let state = "idle"; // 状态流转: idle -> prepare -> running -> stopped -> idle

  // --- 功能函数 ---

  // 魔方打乱公式
  function generateScramble() {
    const faces = ["U", "D", "L", "R", "F", "B"];  // 魔方面
    const modifiers = ["", "'", "2"];  // 旋转修饰符
    const scrambleLength = 20; 
    let scramble = [];
    let lastFace = null;

    for (let i = 0; i < scrambleLength; i++) {
      let face, move;
      do {
        face = faces[Math.floor(Math.random() * faces.length)];  // 随机选择一个面
      } while (face === lastFace);
      move = face + modifiers[Math.floor(Math.random() * modifiers.length)];  // 随机选择一个修饰符
      scramble.push(move);
      lastFace = face;
    }
    return scramble.join("  ");
  }

  // 格式化时间
  function formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const milliseconds = ms % 1000;
    return `${seconds}.${milliseconds.toString().padStart(3, "0")}`;
  }

  // 启动计时器
  function startTimer() {
    startTime = Date.now() - elapsedTime;  // 考虑之前的已过时间
    timer = setInterval(() => {
      elapsedTime = Date.now() - startTime;  // 计算经过的时间
      timeDisplay.textContent = formatTime(elapsedTime);
    }, 10);
  }

  // 停止计时器
  function stopTimer() {
    clearInterval(timer);
    timer = null;
  }

  // 复位计时器
  function resetTimer() {
    elapsedTime = 0;
    timeDisplay.textContent = formatTime(elapsedTime);
  }

  // --- 交互处理 ---

  // 1. 按下 (键盘按下 / 手指触摸)
  function handleDown() {
    // 阶段一：空闲 -> 准备
    if (state === "idle") {
      state = "prepare";
      timeDisplay.classList.add("ready"); // 变绿
    } 
    // 阶段二：计时中 -> 停止
    else if (state === "running") {
      stopTimer();
      state = "stopped";
      timeDisplay.classList.remove("running"); // 移除高亮，变回普通颜色
    } 
    // 阶段三：停止 -> 复位
    else if (state === "stopped") {
      resetTimer();
      const scramble = generateScramble();
      scrambleDisplay.textContent = scramble;
      
      // 回到 idle
      state = "idle"; 
      
      // 移除所有状态类，变回默认的蓝色霓虹效果
      timeDisplay.classList.remove("ready");
      timeDisplay.classList.remove("running");
    }
  }

  // 2. 松开 (键盘抬起 / 手指离开)
  function handleUp() {
    // 只有在“准备状态”松开，才开始计时
    if (state === "prepare") {
      startTimer();
      state = "running";
      
      timeDisplay.classList.remove("ready");
      timeDisplay.classList.add("running"); // 变白高亮
    }
    // 回到了 idle 状态，等待下一次按下。
    else if (state === "idle") {
        timeDisplay.classList.remove("ready");
    }
  }

  // --- 事件监听 ---

  // 初始化
  scrambleDisplay.textContent = generateScramble();

  // 触摸事件
  document.addEventListener("touchstart", (e) => {
    if(e.target.closest('.timer-container')) {
        e.preventDefault(); 
        handleDown();
    }
  }, {passive: false});

  document.addEventListener("touchend", (e) => {
    if(e.target.closest('.timer-container')) {
        handleUp();
    }
  });

  // 键盘事件
  document.addEventListener("keydown", (event) => {
    if (event.code === "Space") {
      event.preventDefault(); 
      if (!event.repeat) {
        handleDown();
      }
    }
  });

  document.addEventListener("keyup", (event) => {
    if (event.code === "Space") {
      handleUp();
    }
  });