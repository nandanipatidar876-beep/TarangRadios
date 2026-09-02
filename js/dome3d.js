/**
 * Tarang Radios - 3D Globe Gallery of Rectangular Category Cards
 * Positions full HTML Rectangular Cards in 3D spherical globe space with 360° touch/mouse drag rotation.
 */

class Globe3DRectangularCards {
  constructor(containerId, categories, onSelectCategory) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.categories = categories;
    this.onSelectCategory = onSelectCategory;

    // Clear previous container contents
    this.container.innerHTML = '';

    this.stage = document.createElement('div');
    this.stage.className = 'globe-3d-stage';

    this.sphere = document.createElement('div');
    this.sphere.className = 'globe-3d-sphere';
    this.stage.appendChild(this.sphere);

    this.container.appendChild(this.stage);

    // Instruction badge
    const instructionPill = document.createElement('div');
    instructionPill.className = 'globe-instruction-pill';
    instructionPill.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v6"/><path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 0 1 2 2v4a6 6 0 0 1-6 6h-2a6 6 0 0 1-6-6v-1a2 2 0 0 1 2-2h12z"/></svg> Drag to rotate 360° • Touch card to expand subcategories`;
    this.container.appendChild(instructionPill);

    this.cardElements = [];
    this.rotX = 0.18;
    this.rotY = 0;
    this.targetRotX = 0.18;
    this.targetRotY = 0;
    this.velocityX = 0;
    this.velocityY = 0.0025;
    this.isDragging = false;
    this.lastMousePos = { x: 0, y: 0 };
    this.radius = 330; // 3D Globe radius in pixels

    this.initCards();
    this.bindEvents();
    this.animate();
  }

  initCards() {
    const total = this.categories.length;

    this.categories.forEach((cat, index) => {
      // Fibonacci spiral distribution on sphere surface
      const phi = Math.acos(1 - 2 * (index + 0.5) / total);
      const theta = Math.PI * (1 + Math.sqrt(5)) * (index + 0.5);

      const x = this.radius * Math.sin(phi) * Math.cos(theta);
      const y = this.radius * Math.cos(phi);
      const z = this.radius * Math.sin(phi) * Math.sin(theta);

      // Create DOM Rectangular Card element
      const cardEl = document.createElement('div');
      cardEl.className = 'globe-rect-card';

      const subChips = cat.subcategories.slice(0, 3).map(sub => `<span class="cat-sub-chip">${sub}</span>`).join('');

      cardEl.innerHTML = `
        <div style="width: 100%; height: 110px; overflow: hidden; border-radius: var(--radius-sm); margin-bottom: 0.55rem; border: 1.5px solid var(--honey-yellow);">
          <img src="${cat.image}" alt="${cat.title}" style="width: 100%; height: 100%; object-fit: cover;" />
        </div>
        <h3 class="medium-cat-title" style="text-align: center; margin: 0; font-size: 0.95rem; font-weight: 800; color: var(--warm-orange); line-height: 1.25;">${cat.title}</h3>
      `;

      cardEl.addEventListener('click', (e) => {
        e.stopPropagation();
        this.onSelectCategory(cat);
      });

      this.sphere.appendChild(cardEl);

      this.cardElements.push({
        element: cardEl,
        baseX: x,
        baseY: y,
        baseZ: z,
        x: x, y: y, z: z
      });
    });
  }

  bindEvents() {
    const startDrag = (x, y) => {
      this.isDragging = true;
      this.lastMousePos = { x, y };
    };

    const moveDrag = (x, y) => {
      if (!this.isDragging) return;
      const deltaX = x - this.lastMousePos.x;
      const deltaY = y - this.lastMousePos.y;

      this.targetRotY += deltaX * 0.005;
      this.targetRotX -= deltaY * 0.005;

      this.velocityY = deltaX * 0.002;
      this.velocityX = -deltaY * 0.002;

      this.lastMousePos = { x, y };
    };

    const stopDrag = () => {
      this.isDragging = false;
    };

    // Mouse Events
    this.container.addEventListener('mousedown', (e) => startDrag(e.clientX, e.clientY));
    window.addEventListener('mousemove', (e) => moveDrag(e.clientX, e.clientY));
    window.addEventListener('mouseup', stopDrag);

    // Touch Events
    this.container.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        startDrag(e.touches[0].clientX, e.touches[0].clientY);
      }
    });

    window.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1) {
        moveDrag(e.touches[0].clientX, e.touches[0].clientY);
      }
    });

    window.addEventListener('touchend', stopDrag);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    if (!this.isDragging) {
      this.targetRotY += this.velocityY;
      this.targetRotX += this.velocityX;

      this.velocityY *= 0.96;
      this.velocityX *= 0.96;

      if (Math.abs(this.velocityY) < 0.0008) this.velocityY = 0.002; // continuous smooth idle orbital spin
    }

    this.rotX += (this.targetRotX - this.rotX) * 0.1;
    this.rotY += (this.targetRotY - this.rotY) * 0.1;

    this.updateCardTransforms();
  }

  updateCardTransforms() {
    const cosX = Math.cos(this.rotX);
    const sinX = Math.sin(this.rotX);
    const cosY = Math.cos(this.rotY);
    const sinY = Math.sin(this.rotY);

    this.cardElements.forEach((item) => {
      // 3D Matrix Rotation
      let x1 = item.baseX * cosY + item.baseZ * sinY;
      let z1 = -item.baseX * sinY + item.baseZ * cosY;

      let y2 = item.baseY * cosX - z1 * sinX;
      let z2 = item.baseY * sinX + z1 * cosX;

      item.x = x1;
      item.y = y2;
      item.z = z2;

      // Perspective Depth Scaling & Opacity Fading
      const fov = 650;
      const scale = Math.max(0.48, fov / (fov - z2));
      const opacity = Math.min(1, Math.max(0.2, (z2 + this.radius) / (this.radius * 2)));
      const zIndex = Math.round(z2 + this.radius);

      const el = item.element;
      el.style.transform = `translate3d(${x1}px, ${y2}px, ${z2}px) scale(${scale})`;
      el.style.opacity = opacity.toFixed(2);
      el.style.zIndex = zIndex;
      el.style.pointerEvents = z2 > -40 ? 'auto' : 'none'; // Allow front-facing cards to be clicked
    });
  }
}
