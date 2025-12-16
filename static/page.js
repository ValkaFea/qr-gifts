(() => {
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  const shareBtn = document.getElementById("shareBtn");
  if (shareBtn) {
    shareBtn.addEventListener("click", async () => {
      const url = window.location.href;
      try {
        if (navigator.share) {
          await navigator.share({ title: document.title, url });
        } else {
          await navigator.clipboard.writeText(url);
          shareBtn.textContent = "Ссылка скопирована ✅";
          setTimeout(() => (shareBtn.textContent = "Поделиться"), 1500);
        }
      } catch (_) {}
    });
  }

  const musicBtn = document.getElementById("musicBtn");
  const audio = document.getElementById("bgMusic");
  if (musicBtn && audio) {
    const src = musicBtn.dataset.music;
    let isOn = false;

    musicBtn.addEventListener("click", async () => {
      try {
        if (!isOn) {
          audio.src = src;
          audio.loop = true;
          audio.volume = 0.6;
          await audio.play();
          isOn = true;
          musicBtn.textContent = "⏸ Пауза";
        } else {
          audio.pause();
          isOn = false;
          musicBtn.textContent = "▶ Включить музыку";
        }
      } catch (e) {
        musicBtn.textContent = "Не удалось включить музыку";
      }
    });
  }
})();
