export function initCodeMode() {
  function render(): string {
    return `
      <div id="layout-code" class="layout-panel">
        <div class="code-sidebar">
          <div class="sidebar-title">FILES</div>
          <div class="file-item active">main.py</div>
          <div class="file-item">cognitive_core.py</div>
          <div class="file-item">config.py</div>
        </div>
        <div class="code-editor">
          <div class="code-line"><span class="kw">def</span> <span class="fn">process</span>(input):</div>
          <div class="code-line">    <span class="cm"># ZARA Cognitive Engine</span></div>
          <div class="code-line">    <span class="kw">return</span> model.generate(input)</div>
        </div>
      </div>
    `;
  }

  return { render };
}
