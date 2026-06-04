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
      <p><strong>${data.brand}</strong></p>
      <p><em>${data.script}</em></p>
      <audio controls src="${data.audio_url}"></audio>
    `;
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
