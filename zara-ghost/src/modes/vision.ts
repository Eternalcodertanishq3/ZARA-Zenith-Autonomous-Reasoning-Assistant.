export function initVisionMode() {
  function render(): string {
    return `
      <div id="layout-vision" class="layout-panel">
        <div class="vision-cam">CAM</div>
        <div class="vision-text-wrap">
          <div class="vision-title">Scene Analysis</div>
          <div class="vision-desc" id="vision-text">Waiting for visual input stream...</div>
        </div>
        <div class="vision-tags">
          <span class="tag">Idle</span>
        </div>
      </div>
    `;
  }

  return { render };
}
