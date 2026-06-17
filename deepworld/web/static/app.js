/* global state */
let currentFile = null;

/* ── Upload Zone ── */
const zone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');

zone.addEventListener('click', () => fileInput.click());
zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
zone.addEventListener('drop', (e) => {
  e.preventDefault();
  zone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});

/* ── File Handler ── */
async function handleFile(file) {
  currentFile = file;
  document.getElementById('uploadStatus').innerHTML = '<span class="spinner"></span> 解析中...';
  document.getElementById('previewSection').classList.add('d-none');
  document.getElementById('errorSection').classList.add('d-none');

  const fd = new FormData();
  fd.append('file', file);

  try {
    const r = await fetch('/api/parse', { method: 'POST', body: fd });
    const data = await r.json();

    if (!data.ok) {
      showError(data.error || '解析失败');
      return;
    }

    showPreview(data.project, file.name);
  } catch (err) {
    showError('网络错误: ' + err.message);
  }
}

function showError(msg) {
  document.getElementById('uploadStatus').innerHTML = '';
  document.getElementById('errorMessage').textContent = msg;
  document.getElementById('errorSection').classList.remove('d-none');
}

/* ── Preview ── */
function showPreview(project, filename) {
  document.getElementById('uploadStatus').innerHTML =
    `<span class="text-success">✅ 解析成功: ${project.clip_count} 个片段</span>`;
  document.getElementById('fileInfo').textContent =
    `${filename} | ${project.source_format.toUpperCase()} | ${project.framerate.toFixed(3)} fps | ${project.timelines.length} 条时间线`;

  document.getElementById('previewSection').classList.remove('d-none');
  document.getElementById('errorSection').classList.add('d-none');

  renderTimelines(project);
}

function renderTimelines(project) {
  const tabList = document.getElementById('tabList');
  const content = document.getElementById('timelineContent');
  tabList.innerHTML = '';
  content.innerHTML = '';

  project.timelines.forEach((tl, ti) => {
    // Tab
    const li = document.createElement('li');
    li.className = 'nav-item';
    li.innerHTML = `<button class="nav-link ${ti === 0 ? 'active' : ''}" data-bs-toggle="tab" data-target="tl-${ti}">${tl.name}</button>`;
    tabList.appendChild(li);
    li.querySelector('button').addEventListener('click', () => {
      tabList.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
      li.querySelector('button').classList.add('active');
      content.querySelectorAll('.tl-content').forEach(d => d.classList.add('d-none'));
      document.getElementById(`tl-content-${ti}`).classList.remove('d-none');
    });

    // Content
    const div = document.createElement('div');
    div.id = `tl-content-${ti}`;
    div.className = `tl-content ${ti === 0 ? '' : 'd-none'}`;
    div.innerHTML = `<p class="text-muted small">${tl.tracks.length} 条轨道</p>`;

    tl.tracks.forEach((tr) => {
      const trackDiv = document.createElement('div');
      trackDiv.className = 'mb-4';
      trackDiv.innerHTML = `<div class="track-header">🎬 ${tr.name} (${tr.type}) — ${tr.clips.length} 个片段</div>`;

      if (tr.clips.length === 0) {
        trackDiv.innerHTML += '<p class="text-muted small px-2">空轨道</p>';
      } else {
        let html = `<div class="table-wrap mt-2"><table class="table table-sm table-bordered table-hover">
          <thead><tr>
            <th>#</th><th>片段名称</th><th>源文件</th><th>源入</th><th>源出</th>
            <th>录制入</th><th>录制出</th><th>时长</th><th>速度</th><th>转场</th>
          </tr></thead><tbody>`;

        tr.clips.forEach(c => {
          html += `<tr>
            <td>${c.index}</td>
            <td>${esc(c.clip_name)}</td>
            <td class="text-truncate" style="max-width:200px">${esc(c.source_file)}</td>
            <td>${c.source_in}</td>
            <td>${c.source_out}</td>
            <td>${c.record_in}</td>
            <td>${c.record_out}</td>
            <td>${c.duration}</td>
            <td>${c.speed}%</td>
            <td>${c.transition}</td>
          </tr>`;

          if (c.markers && c.markers.length) {
            c.markers.forEach(m => {
              html += `<tr class="table-info"><td colspan="2">📍 ${esc(m.name)} @ ${m.tc}</td><td colspan="8"></td></tr>`;
            });
          }
        });

        html += '</tbody></table></div>';
        trackDiv.innerHTML += html;
      }

      div.appendChild(trackDiv);
    });

    content.appendChild(div);
  });
}

/* ── Download ── */
async function downloadFile(format) {
  if (!currentFile) return;

  const fd = new FormData();
  fd.append('file', currentFile);
  fd.append('output_format', format);

  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 导出中...';

  try {
    const r = await fetch('/api/export', { method: 'POST', body: fd });
    if (!r.ok) { alert('导出失败: ' + r.statusText); btn.disabled = false; btn.innerHTML = '❌ 重试'; return; }

    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentFile.name.replace(/\.[^.]+$/, `_report.${format}`);
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('网络错误: ' + err.message);
  }

  btn.disabled = false;
  btn.innerHTML = format === 'docx' ? '📄 Word' : format === 'xlsx' ? '📊 Excel' : '📋 CSV';
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}
