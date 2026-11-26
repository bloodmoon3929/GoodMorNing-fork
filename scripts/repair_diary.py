"""Checked substitutions for the pinned prototype's editing defects."""
from pathlib import Path


def repair(html):
    def replace(old, new):
        nonlocal html
        if html.count(old) != 1:
            raise ValueError('Pinned diary source changed; review editing substitution.')
        html = html.replace(old, new, 1)

    helper = (Path(__file__).resolve().parent.parent / 'server/reference/diary_editing.js').read_text(encoding='utf-8')
    replace('const homeLayoutVersion = 3;', helper + '\nconst homeLayoutVersion = 3;')
    replace('home ? safeSlots[count] : [count ? 74 : 50, count ? 72 - (count - 1) * 46 : 50]',
            'home ? safeSlots[count] : demo ? diaryStickerPosition(count) : [count ? 74 : 50, count ? 72 - (count - 1) * 46 : 50]')
    replace('  const items = activeItems();\n  for (const [id, view] of views)',
            '  const items = activeItems();\n  keepDiaryItemsOnPage(items);\n  for (const [id, view] of views)')
    replace('  if (!editing) placement = null;', '  resetPlacement();\n  if (!editing) cancelDiaryLoads();')
    replace("  if (!draft || saving || event.button !== 0) return;\n  if (placement)",
            "  if (!draft || saving || event.button !== 0 || event.target.closest('input,textarea,button,a,select')) return;\n  if (placement)")
    replace('  post.setPointerCapture(event.pointerId);\n  rebasePlacement();',
            "  event.preventDefault();\n  post.setPointerCapture(event.pointerId);\n  placement.node.classList.add('dragging');\n  rebasePlacement();")
    replace('  const { item, view, node, origin, pose, points, width, height } = placement;',
            '  event.preventDefault();\n  const { item, view, node, origin, pose, points, width, height } = placement;')
    replace("    placement = null;\n    elements.post.classList.remove('safe-placement-blocked');",
            "    placement.node.classList.remove('dragging');\n    placement = null;\n    elements.post.classList.remove('safe-placement-blocked');")
    replace("post.addEventListener('lostpointercapture', endPlacement);",
            "post.addEventListener('lostpointercapture', endPlacement);\nwindow.addEventListener('blur', resetPlacement);\ndocument.addEventListener('visibilitychange', () => { if (document.hidden) resetPlacement(); });\npost.addEventListener('dragstart', event => { if (draft) event.preventDefault(); });")
    start = html.index('  function choosePhoto(index) {')
    end = html.index('\n\nfunction setProductPhoto', start)
    html = html[:start] + '  wireDiaryPhotoUpload(postInput);\n}\n' + html[end:]
    replace("elements.publish.addEventListener('click', async () => {\n  if (saving) return;",
            "elements.publish.addEventListener('click', async () => {\n  if (saving || !draft) return;\n  if (diaryLoads.size) { notice('사진과 스티커를 불러오는 중이에요. 잠시 뒤 게시해 주세요.'); return; }\n  resetPlacement();")
    return html
