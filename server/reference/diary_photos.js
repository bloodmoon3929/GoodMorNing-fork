if (demo) {
  const contents = document.createElement('div');
  contents.className = 'diary-content-plane';
  elements.post.append(contents);
  contents.append(diary, elements.polaroid, elements.layers);
}

function hasPolaroidImage(photo, index) {
  return Boolean(photo.file || photo.source ||
    (index === storyIndex && !newDiaryPage && diaryCards[index]?.querySelector('img')?.dataset.original));
}

// Keep array indexes stable: they identify photos, captions and attachments.
// Order applies only inside the isolated photo plane, below every sticker.
function diaryPhotoStack(photos) {
  return photos.map((photo,index) => ({photo,index}))
    .filter(({photo,index}) => !photo.removed && (index === storyIndex || index >= stories.length) && hasPolaroidImage(photo,index))
    .sort((a,b) => (Number.isFinite(a.photo.layerOrder) ? a.photo.layerOrder : a.index) -
      (Number.isFinite(b.photo.layerOrder) ? b.photo.layerOrder : b.index) || a.index-b.index);
}

function renderPolaroidCaption(card, photo, index, blank) {
  const caption = card.querySelector('figcaption');
  const text = photo.caption ?? (index === storyIndex && !newDiaryPage ? story.title : '');
  // A blank page is not a text card. Keep old data stored, but never draw it on paper.
  if (blank) { caption.replaceChildren(); return; }
  caption.title = text;
  if (!draftDiary || visitingDiary) { caption.textContent = text; return; }
  let input = caption.querySelector('textarea');
  if (!input) {
    input = document.createElement('textarea');
    input.className = 'polaroid-caption-editor';
    input.rows = 2; input.maxLength = 70;
    input.placeholder = '이 사진에 남길 말';
    input.setAttribute('aria-label', '폴라로이드 아래 흰 여백에 메모 쓰기');
    // Writing must not start the photo's drag/rotate gesture or board shortcuts.
    for (const type of ['pointerdown', 'pointermove', 'pointerup', 'keydown']) {
      input.addEventListener(type, event => event.stopPropagation());
    }
    input.addEventListener('focus', () => {
      selectedDiaryPhoto = Number(card.dataset.photoIndex);
      syncDiaryControls();
      for (const other of diaryCards) other.classList.toggle('selected-photo', other === card);
    });
    input.addEventListener('input', () => {
      const selectedIndex = Number(card.dataset.photoIndex);
      const current = draftDiary?.[selectedIndex];
      if (!current) return;
      current.caption = input.value;
      caption.title = input.value;
      if (selectedDiaryPhoto === selectedIndex) document.getElementById('diary-caption-input').value = input.value;
    });
    caption.replaceChildren(input);
  }
  if (document.activeElement !== input) input.value = text;
}
