export function initSystemMode() {
  let timer: number | null = null;

  function startMonitoring(updateCallback: (stats: { cpu: number; ram: number; gpu: number }) => void): void {
    if (timer) clearInterval(timer);
    timer = window.setInterval(() => {
      const cpu = Math.round(15 + Math.random() * 30);
      const ram = Math.round(40 + Math.random() * 20);
      const gpu = Math.round(10 + Math.random() * 25);
      updateCallback({ cpu, ram, gpu });
    }, 2000);
  }

  function stopMonitoring(): void {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  return { startMonitoring, stopMonitoring };
}
