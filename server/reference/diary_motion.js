// Runs in the original diary's scope. Sensor motion changes light, never the book pose.
if (mountedBoard && demo) (() => {
  const board = elements.post;
  const gyro = document.getElementById('enable-tilt');
  const status = document.getElementById('tilt-status');
  const reading = document.getElementById('reading-mode');
  const manual = document.createElement('button');
  manual.type = 'button'; manual.className = 'button'; manual.textContent = '수동 기울이기';
  manual.hidden = true; manual.disabled = true;
  gyro.after(manual);
  const Orientation = window.DeviceOrientationEvent;
  let state = 'checking', enabled = true, origin = null, hasSensor = false;
  let targetX = 0, targetY = 0, lightX = 0, lightY = 0;
  let manualOn = false, manualX = 0, manualY = 0, drag = null;
  let frame = null, timer = null, disposed = false;
  const neutralized = new WeakSet();
  function message(text) { status.textContent = text; status.className = 'distance-status'; }
  function updateControls() {
    manual.disabled = state !== 'unavailable';
    manual.hidden = state !== 'unavailable';
    manual.setAttribute('aria-pressed', String(manualOn));
    gyro.hidden = state === 'unavailable';
    gyro.textContent = state === 'active' && enabled ? '반짝임 켜짐' : '자이로 켜기';
    gyro.title = '휴대폰 기울기로 스티커 반짝임 조절';
    gyro.setAttribute('aria-label', gyro.title);
    gyro.setAttribute('aria-pressed', String(state === 'active' && enabled));
    board.style.touchAction = manualOn ? 'none' : '';
  }
  function stopManual() { manualOn = false; manualX = manualY = 0; drag = null; updateControls(); }
  function paint() {
    frame = null;
    if (disposed) return;
    lightX += (targetX - lightX) * .2; lightY += (targetY - lightY) * .2;
    if (Math.abs(targetX-lightX) < .04) lightX = targetX;
    if (Math.abs(targetY-lightY) < .04) lightY = targetY;
    const x = manualOn && !draft ? manualX : 0, y = manualOn && !draft ? manualY : 0;
    for (const style of [board.style, board.parentElement.style]) {
      style.setProperty('--tilt-x', `${-y}deg`); style.setProperty('--tilt-y', `${x}deg`);
      style.setProperty('--book-zoom', '1'); style.setProperty('--book-pan-x', '0px'); style.setProperty('--book-pan-y', '0px');
    }
    for (const view of views.values()) {
      if (!diaryOpen) continue;
      if (!view.model) mountBoardModel(view);
      if (!view.ready || !view.model) continue;
      if (view.previewFirst) {
        const show = fitBoardAsset(view);
        view.node.classList.toggle('model-ready', Boolean(show));
        if (!show) continue;
      }
      if (!neutralized.has(view.model)) { view.model.setAngle?.(0, 0); neutralized.add(view.model); }
      view.model.setDisplayScale?.(view.liveScale ?? 1);
      view.model.setLightAngle?.(manualOn ? x : lightX, manualOn ? y : lightY);
    }
    if (lightX !== targetX || lightY !== targetY) scheduleBoard();
  }
  scheduleBoard = () => { if (!disposed && frame === null) frame = requestAnimationFrame(paint); };
  stopBoardEffects = () => { stopManual(); scheduleBoard(); };
  function unavailable() {
    if (hasSensor || disposed || document.hidden || state === 'denied' || state === 'permission') return;
    state = 'unavailable'; updateControls();
    message('센서 값을 받지 못했어요. 수동 기울이기를 사용할 수 있어요.');
  }
  function armTimeout() { clearTimeout(timer); timer = setTimeout(unavailable, 6000); }
  function move(event) {
    if (disposed || document.hidden || !Number.isFinite(event.beta) || !Number.isFinite(event.gamma)) return;
    const justConnected = !hasSensor || state !== 'active';
    hasSensor = true; clearTimeout(timer); state = 'active';
    if (manualOn) stopManual();
    if (justConnected) updateControls();
    if (!enabled) return;
    if (!origin) origin = { beta: event.beta, gamma: event.gamma };
    const delta = (v, start) => ((v-start+540)%360)-180;
    const dx = delta(event.gamma, origin.gamma), dy = delta(event.beta, origin.beta);
    const angle = (screen.orientation?.angle ?? window.orientation ?? 0) * Math.PI / 180;
    targetX = clamp(dx*Math.cos(angle) + dy*Math.sin(angle), -32, 32);
    targetY = clamp(dy*Math.cos(angle) - dx*Math.sin(angle), -32, 32);
    if (justConnected) message('휴대폰을 기울이면 스티커의 반짝임이 움직여요.');
    scheduleBoard();
  }
  async function detectPermission() {
    for (const name of ['accelerometer', 'gyroscope']) {
      try { if ((await navigator.permissions.query({name})).state === 'denied') return false; } catch {}
    }
    return true;
  }
  function denied() {
    state = 'denied'; enabled = false; clearTimeout(timer); stopManual();
    message('센서 접근이 허용되지 않았어요. 브라우저에서 동작 센서 권한을 허용해 주세요.');
  }
  async function begin(fromClick = false) {
    if (!Orientation || !window.isSecureContext) { unavailable(); return; }
    if (typeof Orientation.requestPermission === 'function') {
      if (!fromClick) { state = 'permission'; updateControls(); message('자이로 켜기를 눌러 동작 센서를 허용해 주세요.'); return; }
      try { if (await Orientation.requestPermission() !== 'granted') { denied(); return; } }
      catch { denied(); return; }
    }
    if (!await detectPermission()) { denied(); return; }
    if (disposed) return;
    state = hasSensor ? 'active' : 'checking'; enabled = true; origin = null;
    stopManual(); window.addEventListener('deviceorientation', move);
    message(hasSensor ? '휴대폰을 기울이면 스티커의 반짝임이 움직여요.' : '휴대폰 동작 센서를 확인하고 있어요.'); armTimeout();
  }
  gyro.addEventListener('click', () => {
    if (state === 'active' && enabled) {
      enabled = false; targetX = targetY = 0; updateControls(); scheduleBoard();
      message('반짝임 움직임을 멈췄어요. 다시 켜면 현재 자세를 기준으로 움직여요.');
    } else void begin(true);
  });
  manual.addEventListener('click', () => {
    if (state !== 'unavailable') return;
    manualOn = !manualOn; manualX = manualY = 0; drag = null;
    updateControls(); scheduleBoard();
    message(manualOn ? '다이어리를 드래그하거나 방향키로 기울여 보세요. 편집 중에는 기울이지 않아요.' : '수동 기울이기를 껐어요.');
  });
  board.tabIndex = 0;
  board.addEventListener('pointerdown', event => {
    if (!manualOn || draft || !event.isPrimary || event.button !== 0 || event.target.closest('button,a,input,select,textarea')) return;
    drag = { id:event.pointerId, sx:event.clientX, sy:event.clientY, x:manualX, y:manualY };
    board.setPointerCapture(event.pointerId); event.preventDefault();
  });
  board.addEventListener('pointermove', event => {
    if (!manualOn || draft || drag?.id !== event.pointerId) return;
    manualX = clamp(drag.x+(event.clientX-drag.sx)*.25,-32,32);
    manualY = clamp(drag.y+(event.clientY-drag.sy)*.25,-32,32); scheduleBoard();
  });
  for (const type of ['pointerup','pointercancel','lostpointercapture']) board.addEventListener(type, () => { drag=null; });
  board.addEventListener('keydown', event => {
    if (!manualOn || draft || event.target !== board) return;
    if (event.key === 'Escape') { stopManual(); scheduleBoard(); return; }
    const step = {ArrowLeft:[-3,0],ArrowRight:[3,0],ArrowUp:[0,-3],ArrowDown:[0,3]}[event.key];
    if (!step) return;
    event.preventDefault(); manualX=clamp(manualX+step[0],-32,32); manualY=clamp(manualY+step[1],-32,32); scheduleBoard();
  });
  function readingMode(active) {
    document.body.classList.toggle('reading-mode',active); reading.setAttribute('aria-pressed',String(active));
    reading.title = active ? '전체화면 닫기' : '전체화면 켜기'; reading.setAttribute('aria-label',reading.title);
  }
  reading.hidden=false;
  reading.addEventListener('click',async()=>{
    const active=!document.body.classList.contains('reading-mode'); readingMode(active);
    try { if(active) await document.documentElement.requestFullscreen?.(); else if(document.fullscreenElement) await document.exitFullscreen?.(); } catch {}
  });
  document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement)readingMode(false);});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')readingMode(false);});
  const rebase=()=>{origin=null; targetX=targetY=0; scheduleBoard();};
  window.addEventListener('orientationchange',rebase);
  screen.orientation?.addEventListener('change',rebase);
  document.addEventListener('visibilitychange',()=>{
    clearTimeout(timer); if(!document.hidden){rebase();if(state==='checking')armTimeout();}
  });
  window.addEventListener('pagehide',()=>{
    disposed=true; clearTimeout(timer); cancelAnimationFrame(frame); window.removeEventListener('deviceorientation',move);
    window.removeEventListener('orientationchange',rebase); screen.orientation?.removeEventListener('change',rebase);
  });
  updateControls(); scheduleBoard(); void begin();
})();
