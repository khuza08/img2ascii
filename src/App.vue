<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { openPath } from "@tauri-apps/plugin-opener";

interface ConversionResult {
  image_path: string;
  image_base64: string;
  txt_path: string;
}

const filepath = ref("");
const filename = ref("No image selected");
const outputName = ref("ascii_output");
const scaleFactor = ref(0.1);
const brightness = ref(1.0);
const contrast = ref(1.0);
const saturation = ref(1.0);
const isConverting = ref(false);

const resultImagePath = ref("");
const displayImagePath = ref("");



async function convert() {
  if (!filepath.value) return;
  
  isConverting.value = true;
  try {
    const result = await invoke<ConversionResult>("convert_image", {
      params: {
        filepath: filepath.value,
        output_name: outputName.value,
        scale_factor: scaleFactor.value,
        brightness: brightness.value,
        contrast: contrast.value,
        saturation: saturation.value
      }
    });
    
    resultImagePath.value = result.image_path;
    displayImagePath.value = result.image_base64;
  } catch (error) {
    console.error(error);
  } finally {
    isConverting.value = false;
  }
}

async function openResultImage() {
  if (resultImagePath.value) {
    try {
      await openPath(resultImagePath.value);
    } catch (error) {
      console.error("Failed to open image:", error);
    }
  }
}

// Initial convert on load logic elsewhere...



// Watch filepath to trigger initial conversion
watch(filepath, () => {
  if (filepath.value) {
    convert();
  }
});

async function selectImage() {
  const selected = await open({
    multiple: false,
    filters: [{
      name: 'Image',
      extensions: ['png', 'jpg', 'jpeg', 'bmp', 'gif']
    }]
  });
  if (selected && !Array.isArray(selected)) {
    filepath.value = selected;
    filename.value = selected.split(/[/\\]/).pop() || selected;
  }
}

onMounted(async () => {
  // Correct method name for Tauri v2 is onDragDropEvent
  (getCurrentWindow() as any).onDragDropEvent((event: any) => {
    if (event.payload.type === 'drop') {
      const droppedPath = event.payload.paths[0];
      if (droppedPath) {
        filepath.value = droppedPath;
        filename.value = droppedPath.split(/[/\\]/).pop() || droppedPath;
      }
    }
  });

  // Show window once UI is ready (Anti-Flashbang)
  await getCurrentWindow().show();
});
</script>

<template>
  <div class="app-container">
    <aside class="sidebar">
      <div class="logo-section">
        <h1>img2ascii</h1>
        <p class="subtitle">by khuza08 (Pure Rust)</p>
      </div>

      <div class="control-group">
        <label>Input</label>
        <div class="file-picker" @click="selectImage">
          <div class="icon">📁</div>
          <div class="file-info">
            <span class="file-name">{{ filename }}</span>
          </div>
        </div>
      </div>

      <div class="control-group">
        <label>Output Filename</label>
        <input v-model="outputName" placeholder="filename" class="text-input" />
      </div>



      <div class="control-group sliders">
        <div class="slider-item">
          <div class="slider-header">
            <span>Scale Factor</span>
            <span class="value">{{ scaleFactor.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="scaleFactor" min="0.05" max="1.0" step="0.01" @change="convert" />
        </div>

        <div class="slider-item">
          <div class="slider-header">
            <span>Brightness</span>
            <span class="value">{{ brightness.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="brightness" min="0.5" max="2.0" step="0.05" @change="convert" />
        </div>

        <div class="slider-item">
          <div class="slider-header">
            <span>Contrast</span>
            <span class="value">{{ contrast.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="contrast" min="0.5" max="2.0" step="0.05" @change="convert" />
        </div>

        <div class="slider-item">
          <div class="slider-header">
            <span>Saturation</span>
            <span class="value">{{ saturation.toFixed(2) }}</span>
          </div>
          <input type="range" v-model.number="saturation" min="0.5" max="2.0" step="0.05" @change="convert" />
        </div>
      </div>

      <button 
        class="convert-btn" 
        :disabled="!filepath || isConverting" 
        @click="resultImagePath ? openResultImage() : convert()"
      >
        <span v-if="!isConverting">
          {{ resultImagePath ? 'Open Result Image' : (filepath ? 'Live Mode Active' : 'Convert (Rust Engine)') }}
        </span>
        <span v-else class="loader"></span>
      </button>
    </aside>

    <main class="content">
      <div class="viewer-container">
        <div class="image-viewer">
          <div v-if="displayImagePath" class="image-preview-container">
            <img :src="displayImagePath" alt="ASCII Art" class="ascii-image" />
            <div class="image-path-info mini">
              <code>{{ resultImagePath }}</code>
            </div>
          </div>
          <div v-else class="placeholder">
            {{ isConverting ? 'Processing Image...' : 'Select an image to start' }}
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style>
/* (Existing styles start here) */
:root {
  --bg-dark: #0f172a;
  --bg-sidebar: rgba(15, 23, 42, 0.8);
  --accent: #10b981; /* Green for Rust */
  --accent-glow: rgba(16, 185, 129, 0.3);
  --text-main: #f8fafc;
  --text-dim: #94a3b8;
  --glass-border: rgba(255, 255, 255, 0.1);
}

body {
  margin: 0;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background-color: var(--bg-dark);
  color: var(--text-main);
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}

/* Sidebar */
.sidebar {
  width: 320px;
  background: var(--bg-sidebar);
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--glass-border);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-sizing: border-box;
}

.logo-section h1 {
  margin: 0;
  font-size: 1.5rem;
  background: linear-gradient(to right, #10b981, #3b82f6);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: var(--text-dim);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dim);
  font-weight: 600;
}

.file-picker {
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed var(--glass-border);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.file-picker:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent);
  box-shadow: 0 0 20px var(--accent-glow);
}

.icon {
  font-size: 1.5rem;
}

.file-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.file-name {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.text-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  padding: 10px 12px;
  color: white;
  outline: none;
  transition: border-color 0.2s;
}

.text-input:focus {
  border-color: var(--accent);
}

.radio-group {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 4px;
}

.radio-group button {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-dim);
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.radio-group button.active {
  background: var(--accent);
  color: white;
  font-weight: 600;
}

/* Sliders */
.sliders {
  gap: 12px;
}

.slider-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
}

.slider-header .value {
  color: var(--accent);
  font-family: monospace;
}

input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  outline: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  background: var(--accent);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 8px var(--accent-glow);
}

.convert-btn {
  margin-top: auto;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.convert-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.convert-btn:active:not(:disabled) {
  transform: translateY(0);
}

.convert-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  filter: grayscale(1);
}

/* Content */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #020617;
}

.viewer-container {
  flex: 1;
  padding: 24px;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.image-viewer {
  display: flex;
  flex: 1;
  justify-content: center;
  align-items: center;
}

.placeholder {
  height: 100%;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--text-dim);
  font-style: italic;
  font-size: 0.9rem;
  text-align: center;
}

.image-path-info {
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.image-path-info code {
  display: block;
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 6px;
  word-break: break-all;
  color: var(--accent);
}
.image-path-info.mini {
  padding: 8px 16px;
  font-size: 0.75rem;
}

.image-preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.ascii-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--glass-border);
}

.loader {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive Design */
@media (max-width: 900px) {
  .app-container {
    flex-direction: column;
    overflow: auto;
  }

  .sidebar {
    width: 100%;
    height: auto;
    max-height: 400px;
    border-right: none;
    border-bottom: 1px solid var(--glass-border);
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .content {
    min-height: 400px;
  }

  .ascii-image {
    max-height: 50vh;
  }

  .viewer-container {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .sidebar {
    padding: 16px;
    max-height: 350px;
  }

  .logo-section h1 {
    font-size: 1.2rem;
  }

  .convert-btn {
    padding: 12px;
    font-size: 0.9rem;
  }
}
</style>