"""Small storage/navigation substitutions around the original diary UI."""
from pathlib import Path

def adapt(html):
    reference = Path(__file__).resolve().parent.parent / 'server/reference'
    photos = (reference / 'diary_photos.js').read_text(encoding='utf-8')
    photo_css = (reference / 'diary_photos.css').read_text(encoding='utf-8')
    html = html.replace('</head>', '<style>' + photo_css + '</style>\n</head>', 1)
    html = html.replace('const homeLayoutVersion = 3;', photos + '\nconst homeLayoutVersion = 3;', 1)
    html = html.replace("    caption.textContent = photo.caption ?? (index === storyIndex && !newDiaryPage ? story.title : '');\n    caption.title = caption.textContent;", "    renderPolaroidCaption(card, photo, index, blank);")
    html = html.replace("!photo.removed && (index === storyIndex || index >= stories.length) ? [index] : []", "!photo.removed && hasPolaroidImage(photo, index) && (index === storyIndex || index >= stories.length) ? [index] : []")
    html = html.replace("caption.addEventListener('input', () => { const photo = selected(); if (photo) { photo.caption = caption.value; renderDiary(); } });", "caption.addEventListener('input', () => { const photo = selected(); if (photo && hasPolaroidImage(photo, selectedDiaryPhoto)) { photo.caption = caption.value; renderDiary(); } });")
    html = html.replace('>사진 추가</button>', '>폴라로이드 추가</button>')
    html = html.replace('사진 메모 <input id="diary-caption-input"', '폴라로이드 아래 메모 <input id="diary-caption-input"')
    html = html.replace('placeholder="이 사진에 남길 말"', 'placeholder="사진 아래 흰 여백에 남길 말"')
    html = html.replace('        layout[index].file = file;', "        layout[index].file = file;\n        layout[index].caption ??= '';")
    html = html.replace('          base.file = file;', "          base.file = file;\n          base.caption ??= '';")
    html = html.replace('if (mountedBoard) {\n  const tiltButton', 'if (mountedBoard && !demo) {\n  const tiltButton', 1)
    motion = (Path(__file__).resolve().parent.parent / 'server/reference/diary_motion.js').read_text(encoding='utf-8')
    html = html.replace('const homeLayoutVersion = 3;', motion + '\nconst homeLayoutVersion = 3;', 1)
    html = html.replace('</head>', '<script src="./diary_bridge.js"></script>\n</head>')
    html = html.replace('async function readPost() {', '''async function readPost() {
  if (demo && !visitingDiary) return window.goodmorningBridge.readPost(postKey);''')
    html = html.replace('async function writePost(items, photo, diaryLayout) {', '''async function writePost(items, photo, diaryLayout) {
  if (demo && !visitingDiary) return window.goodmorningBridge.writePost(postKey, {items, photo, diaryLayout, diaryLayoutVersion});''')
    start = html.index('async function renderDiaryPages() {')
    tail = html.index('  diaryPages.replaceChildren();', start)
    html = html[:start] + '''async function renderDiaryPages() {
  if (!numberedDiary) return;
  const keys = await window.goodmorningBridge.pageKeys();
  let maxPage = 1;
  for (const key of keys) {
    if (typeof key === 'string' && /^page:\\d+$/.test(key)) maxPage = Math.max(maxPage, Number(key.slice(5)));
  }
''' + html[tail:]
    html = html.replace("function stickerLibrary(mode = 'readonly', asset) {", """function stickerLibrary(mode = 'readonly', asset) {
  if (demo && !visitingDiary && mode === 'readonly') return window.goodmorningBridge.stickers();""")
    html = html.replace('function addItem(asset) {', '''function addItem(asset) {
  if (asset.backendAssetId && !asset.file) {
    void window.goodmorningBridge.materialize(asset).then(addItem).catch(error => notice(error.message));
    return;
  }''')
    start = html.index("elements.publish.addEventListener('click', async () => {")
    end = html.index('\nfunction wireAssetPreview()', start)
    block = html[start:end]
    block = block.replace('  const photo = draftPhoto;\n', '  const photo = draftPhoto;\n  let stored = false;\n')
    block = block.replace('    await writePost(items, photo, draftDiary);', '    await writePost(items, photo, draftDiary);\n    stored = true;')
    block = block.replace("  } catch {\n    notice('이 브라우저에 저장하지 못했습니다. 현재 화면에서만 게시물이 유지됩니다.');", "  } catch (error) {\n    notice(error.message || '저장하지 못했어요. 편집 내용은 그대로 있으니 다시 게시해 주세요.');")
    block = block.replace('    published = items;', '    if (stored) {\n    published = items;')
    block = block.replace('    draft = null;', '    draft = null;\n    }')
    block = block.replace('    elements.edit.focus();', '    if (stored) elements.edit.focus();')
    html = html[:start] + block + html[end:]
    html = html.replace('}).catch(() => {}).finally(() => {', """}).catch(error => {
  if (demo && !visitingDiary) {
    window.goodmorningReadFailed = true;
    notice(error.message || '다이어리를 불러오지 못했어요. 다시 열어 주세요.');
  }
}).finally(() => {""")
    html = html.replace('  elements.edit.disabled = false;\n  if (newDiaryPage && !pageExists) elements.edit.click();', '''  elements.edit.disabled = Boolean(window.goodmorningReadFailed);
  if (newDiaryPage && !pageExists && !window.goodmorningReadFailed) elements.edit.click();
  if (demo && !visitingDiary && !window.goodmorningReadFailed) window.goodmorningBridge.markReady();''')
    return html
