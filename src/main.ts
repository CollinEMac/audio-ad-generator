interface Brand {
  id: string;
  brandName: string;
}

async function loadBrands(): Promise<void> {
  const res = await fetch('/static/exampleBrands.json');
  const brands: Brand[] = await res.json();
  const select = document.getElementById('brand-select') as HTMLSelectElement;

  brands.forEach((brand) => {
    const option = document.createElement('option');
    option.value = brand.id;
    option.textContent = brand.brandName;
    select.appendChild(option);
  });
}

async function handleSubmit(e: SubmitEvent): Promise<void> {
  e.preventDefault();

  const btn = document.getElementById('submit-btn') as HTMLButtonElement;
  const result = document.getElementById('result') as HTMLDivElement;

  // Bail out if there is an invalid selection.
  const select = document.getElementById('brand-select') as HTMLSelectElement;
  if (!select.value) {
    result.textContent = 'Please select a brand.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Generating...';
  result.textContent = '';

  try {
    const formData = new FormData(e.target as HTMLFormElement);
    const res = await fetch('/generate-ad', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json() as { audio_url: string; script: string; brand: string };
    result.innerHTML = `
      <div class="mt-4 text-left">
        <p class="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-1">Generated Ad</p>
        <p class="text-xl font-bold text-slate-900 mb-3">${data.brand}</p>
        <p class="text-slate-700 italic leading-relaxed mb-5">${data.script}</p>
        <audio controls src="${data.audio_url}" class="w-full"></audio>
       </div>
    `;
  } catch {
    result.textContent = 'Something didn\'t go quite right... Give it another shot.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Submit';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadBrands().catch(console.error);
  const form = document.getElementById('ad-form') as HTMLFormElement;
  form.addEventListener('submit', handleSubmit);
});
