// Initialize Lucide Icons
lucide.createIcons();

// Mobile Navigation Toggle
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
menuBtn.addEventListener('click', () => {
  mobileMenu.classList.toggle('hidden');
});

// Populate Alphabet Flip Cards
const carouselContainer = document.getElementById('carousel-container');
const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split('');
// Duplicate 2x for seamless continuous loop marquee
const doubleLetters = [...letters, ...letters]; 

doubleLetters.forEach((letter) => {
  const cardWrapper = document.createElement('div');
  cardWrapper.className = 'relative w-56 h-72 perspective cursor-pointer flex-shrink-0 mx-4 select-none';

  cardWrapper.innerHTML = `
    <div class="card-inner w-full h-full preserve-3d transition-transform duration-700">
      <!-- Front -->
      <div class="absolute inset-0 backface-hidden bg-gradient-to-br from-[#F0EBFF] to-white rounded-3xl flex flex-col items-center justify-center border-2 border-[#DCEBFF] shadow-lg hover:shadow-xl transition-shadow">
        <span class="text-8xl font-black text-[#6346D8]">${letter}</span>
        <span class="absolute bottom-4 text-xs font-semibold text-[#A78BFA] tracking-widest uppercase">Klik untuk lihat</span>
      </div>
      <!-- Back -->
      <div class="absolute inset-0 backface-hidden bg-white rounded-3xl flex flex-col items-center p-4 border-2 border-[#A78BFA] shadow-lg rotate-y-180">
        <div class="w-full flex-1 bg-[#F8F6FF] rounded-2xl mb-3 flex items-center justify-center overflow-hidden border border-[#F0EBFF]">
          <span class="text-sm font-bold text-[#6346D8]">[Foto Isyarat ${letter}]</span>
        </div>
        <div class="text-center w-full">
          <h4 class="text-lg font-bold text-[#19143A]">Isyarat '${letter}'</h4>
          <p class="text-xs text-gray-500 mt-1">Genggam tangan seperti pola ini</p>
        </div>
      </div>
    </div>
  `;

  // 3D Flip Click Interaction
  const innerCard = cardWrapper.querySelector('.card-inner');
  cardWrapper.addEventListener('click', (e) => {
    e.stopPropagation();
    innerCard.classList.toggle('rotate-y-180');
  });

  carouselContainer.appendChild(cardWrapper);
});

// Arrow Nav Controls for Marquee Scroll Shift
const marqueeContainer = document.getElementById('carousel-container');

document.getElementById('scroll-left').addEventListener('click', () => {
  const currentTransform = new WebKitCSSMatrix(window.getComputedStyle(marqueeContainer).transform);
  marqueeContainer.style.transform = `translateX(${currentTransform.m41 + 320}px)`; 
});

document.getElementById('scroll-right').addEventListener('click', () => {
  const currentTransform = new WebKitCSSMatrix(window.getComputedStyle(marqueeContainer).transform);
  marqueeContainer.style.transform = `translateX(${currentTransform.m41 - 320}px)`;
});
