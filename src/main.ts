interface Brand {
  id: string;
  brandName: string;
}

interface GenerateAdResponse {
  message: string;
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

  btn.disabled = true;
  btn.textContent = 'Generating...';
  result.textContent = '';

  try {
    const formData = new FormData(e.target as HTMLFormElement);
    const res = await fetch('/generate-ad', {
      method: 'POST',
      body: formData,
    });
    const data: GenerateAdResponse = await res.json();
    result.textContent = data.message;
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
