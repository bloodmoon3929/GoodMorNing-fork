// Editor state shared by local photos and asynchronous library insertion.
let diaryPhotoRequest = null;
const diaryLoads = new Set();
function beginDiaryLoad() {
  const token = {};
  diaryLoads.add(token);
  elements.publish.disabled = true;
  return token;
}
function endDiaryLoad(token) {
  diaryLoads.delete(token);
  elements.publish.disabled = saving || diaryLoads.size > 0;
}
function cancelDiaryLoads() {
  diaryPhotoRequest = null;
  diaryLoads.clear();
  elements.publish.disabled = saving;
}
function diaryStickerPosition(count) {
  return [[35, 30], [70, 30], [35, 55], [70, 55], [35, 80], [70, 80]][count % 6];
}
function keepDiaryItemsOnPage(items) {
  if (!demo) return;
  for (const item of items) {
    item.x = clamp(Number.isFinite(item.x) ? item.x : 50, 8, 92);
    item.y = clamp(Number.isFinite(item.y) ? item.y : 50, 8, 92);
  }
}
function resetPlacement() {
  const previous = placement;
  placement = null;
  if (!previous) return;
  previous.node.classList.remove('dragging');
  for (const id of previous.points.keys()) {
    if (post.hasPointerCapture(id)) post.releasePointerCapture(id);
  }
  elements.post.classList.remove('safe-placement-blocked');
}

function wireDiaryPhotoUpload(input) {
  const tap = (id, handler) => document.getElementById(id).addEventListener('click', handler);
  function choose(index) {
    if (!draftDiary || saving) return;
    diaryPhotoRequest = { layout: draftDiary, index };
    input.value = '';
    input.click();
  }
  tap('diary-photo-add', () => choose(null));
  tap('diary-photo-replace', () => choose(selectedDiaryPhoto));
  tap('diary-photo-remove', () => {
    const photo = draftDiary?.[selectedDiaryPhoto];
    if (!photo || saving) return;
    resetPlacement();
    photo.removed = true;
    delete photo.file;
    syncDiaryControls(); renderDiary();
  });
  input.addEventListener('cancel', () => { diaryPhotoRequest = null; });
  input.addEventListener('change', async event => {
    event.stopImmediatePropagation();
    const [file] = input.files;
    input.value = '';
    const request = diaryPhotoRequest;
    if (!file || !request || request.layout !== draftDiary || saving) return;
    const token = beginDiaryLoad();
    let url;
    const current = () => diaryPhotoRequest === request && draftDiary === request.layout && !saving;
    try {
      if (file.size > 16 * 1024 * 1024) throw new Error('사진은 16MB 이하로 선택해 주세요.');
      url = URL.createObjectURL(file);
      const image = new Image();
      image.src = url;
      try { await image.decode(); }
      catch { throw new Error('사진을 열 수 없어요. JPG, PNG 또는 WebP 사진을 선택해 주세요.'); }
      if (!current()) return;
      if (image.naturalWidth * image.naturalHeight > 24000000) throw new Error('사진은 2,400만 화소 이하로 선택해 주세요.');
      if (Math.min(image.naturalWidth, image.naturalHeight) < 32) throw new Error('사진의 가로·세로는 32px 이상이어야 해요.');
      resetPlacement();
      const { layout, index } = request;
      if (index != null) {
        if (!layout[index] || layout[index].removed) return;
        layout[index].file = file;
        layout[index].caption ??= '';
        selectedDiaryPhoto = index;
      } else {
        const base = layout[storyIndex];
        if (newDiaryPage && base && !base.removed && !hasPolaroidImage(base, storyIndex)) {
          base.file = file; base.caption = '';
          selectedDiaryPhoto = storyIndex;
        } else {
          const reusable = layout.findIndex((photo, i) => i >= stories.length && photo.removed);
          if (reusable < 0 && layout.length >= 100) throw new Error('이 장의 사진이 가득 찼어요. 새 장에 추가해 주세요.');
          selectedDiaryPhoto = reusable >= 0 ? reusable : layout.length;
          layout[selectedDiaryPhoto] = { x: 30, y: 37, size: 38, rotation: 0, tape: 'kraft', file, caption: '' };
        }
      }
      notice(); renderDiary(); syncDiaryControls();
    } catch (error) {
      if (current()) notice(error.message || '사진을 추가하지 못했어요. 다시 선택해 주세요.');
    } finally {
      if (url) URL.revokeObjectURL(url);
      if (diaryPhotoRequest === request) diaryPhotoRequest = null;
      endDiaryLoad(token);
    }
  });
}
